"""Document lifecycle, tab navigation and per-document state."""

import tempfile
import uuid
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

import pymupdf as fitz

from grafiplot.constants import ARCHIVES
from grafiplot.core.archives import unpack_archive
from grafiplot.core.conversion import make_pdf
from grafiplot.core.merge import combined_destination

TAB_VARIABLES = (
    "path",
    "mode",
    "grid_type",
    "paper",
    "orientation",
    "margin",
    "overlap",
    "cols",
    "rows",
    "cw",
    "ch",
    "page",
    "print_order",
    "excluded_pages",
    "scale",
    "per_sheet",
    "printer",
    "client",
    "duplex",
    "book_price",
    "copies",
    "content_pct",
    "autorotate",
    "group_name",
    "nup_layout",
    "nup_cols",
    "nup_rows",
    "nup_width",
    "nup_height",
    "nup_center",
    "poster_whole",
)
TAB_COLLECTIONS = (
    "selected_pages",
    "sent_pages",
    "last_export_pages",
    "job_log",
    "crops",
    "free_crops",
)


class DocumentsMixin:
    def _state(self):
        state = {name: getattr(self, name).get() for name in TAB_VARIABLES}
        state.update({name: getattr(self, name).copy() for name in TAB_COLLECTIONS})
        state.update(
            source=self.source,
            document=self.document,
            anchor_page=self.anchor_page,
            last_output=self.last_output,
            source_preview_page=self.source_preview_page,
            zoom=self.zoom,
        )
        return state

    def _restore(self, state):
        self.switching_tabs = True
        try:
            self.document = state["document"]
            self.source = state["source"]
            for key in TAB_VARIABLES:
                getattr(self, key).set(state[key])
            for key in TAB_COLLECTIONS:
                setattr(self, key, state[key].copy())
            self.anchor_page = state["anchor_page"]
            self.last_output = state["last_output"]
            self.zoom = state.get("zoom", 1.0)
            if self.preview_doc:
                self.preview_doc.close()
            self.preview_doc = None
            self.prepared_preview = None
            self.preview_page.set(1)
            self.source_preview_page = state.get("source_preview_page", 0)
            self._crop_mode = False
            self._crop_anchor = None
            self.canvas.configure(cursor="")
            self.canvas.xview_moveto(0)
            self.canvas.yview_moveto(0)
            self.update_mode_controls()
            self.update_thumbnails()
            self.update_tab_colors()
        finally:
            self.switching_tabs = False
        self.update_action_state()
        self.preview()
        self.schedule_preview()

    def scroll_tab_strip(self, event):
        units = -3 if event.delta > 0 else 3
        self.tab_scroll_canvas.xview_scroll(units, "units")
        return "break"

    def focus_tab_strip_item(self, tabid):
        button = getattr(self, "tab_buttons", {}).get(tabid)
        if not button:
            return
        self.update_idletasks()
        width = max(1, self.tab_scroll_frame.winfo_width())
        viewport = max(1, self.tab_scroll_canvas.winfo_width())
        left = self.tab_scroll_canvas.canvasx(0)
        x = button.winfo_x()
        right = x + button.winfo_width()
        if x < left:
            self.tab_scroll_canvas.xview_moveto(max(0, x - 10) / width)
        elif right > left + viewport:
            self.tab_scroll_canvas.xview_moveto(
                min(1, max(0, right - viewport + 10) / width)
            )

    def navigate_tabs(self, delta):
        ids = self.tabs.tabs()
        if not ids:
            return "break"
        selected = self.tabs.select()
        index = ids.index(selected) if selected in ids else 0
        self.tabs.select(ids[(index + delta) % len(ids)])
        self.tabs.focus_set()
        self.focus_tab_strip_item(self.tabs.select())
        return "break"

    def tabs_wheel(self, event):
        delta = -1 if event.delta > 0 else 1
        return self.navigate_tabs(delta)

    def on_tab_changed(self, event=None):
        if self.switching_tabs:
            return
        target = self.tabs.select()
        if not target or target == self.active_tab:
            return
        if self.active_tab in self.tabs_data:
            if self._skip_save_tab != self.active_tab:
                self.tabs_data[self.active_tab] = self._state()
            self._skip_save_tab = None
        self.active_tab = target
        if target in self.tabs_data:
            self._restore(self.tabs_data[target])
        self.focus_tab_strip_item(target)

    def close_tab(self):
        tab = self.tabs.select()
        if not tab:
            return
        if tab == self.active_tab:
            self.tabs_data[tab] = self._state()
        state = self.tabs_data.pop(tab, None)
        self.active_tab = None
        self.tabs.forget(tab)
        self.nametowidget(tab).destroy()
        self._tab_images.pop(tab, None)
        if state and state["document"]:
            state["document"].close()
        group = state.get("group_name", "").strip() if state else ""
        if group:
            self.groups.setdefault(group, []).extend(state.get("job_log", []))
        if self.tabs.tabs():
            self.on_tab_changed()
        else:
            self.document = None
            self.source = None
            self.crops = {}
            self.free_crops = {}
            self.path.set("Ningún archivo seleccionado")
            if self.preview_doc:
                self.preview_doc.close()
                self.preview_doc = None
            self.prepared_preview = None
            self.last_output = None
            self.selected_pages.clear()
            self.sent_pages.clear()
            self.last_export_pages.clear()
            self.job_log.clear()
            self._crop_mode = False
            self._crop_anchor = None
            self.canvas.configure(cursor="")
            self.update_tab_colors()
            self.update_thumbnails()
            self.refresh_price()
            self.preview()
            self.preview_status.configure(
                text="Abre un archivo y prepara su vista de impresión."
            )
        self.update_action_state()

    def open_file(self):
        paths = filedialog.askopenfilenames(
            title="Abrir varios PDF, imágenes o documentos",
            filetypes=[
                (
                    "PDF, imágenes y documentos",
                    "*.pdf *.svg *.png *.jpg *.jpeg *.bmp *.tif *.tiff *.webp *.gif *.doc *.docx *.xls *.xlsx *.ppt *.pptx *.odt *.ods *.odp *.rtf *.txt",
                ),
                ("Todos los archivos", "*.*"),
            ],
        )
        if paths:
            self.open_paths(paths)

    def open_paths(self, paths):
        if self.active_tab in self.tabs_data:
            if self._skip_save_tab != self.active_tab:
                self.tabs_data[self.active_tab] = self._state()
            self._skip_save_tab = None
        errors = []
        opened = []
        for p in paths:
            doc = None
            try:
                directory = tempfile.mkdtemp(prefix="archivo_", dir=self.tmp.name)
                converted = make_pdf(str(p), directory)
                doc = fitz.open(converted)
                if doc.needs_pass:
                    raise ValueError("PDF protegido con contraseña.")
                if not doc.page_count:
                    raise ValueError("Documento sin páginas.")
                tab = ttk.Frame(self.tabs)
                self.tabs.add(tab, text=Path(p).name[:28])
                tid = str(tab)
                state = self._state()
                state.update(
                    source=converted,
                    document=doc,
                    path=Path(p).name,
                    mode="Normal",
                    per_sheet="1",
                    nup_layout="Automática",
                    nup_cols="2",
                    nup_rows="2",
                    nup_width="50",
                    nup_height="70",
                    source_preview_page=0,
                    zoom=1.0,
                    duplex=False,
                    selected_pages=set(),
                    sent_pages=set(),
                    last_export_pages=set(),
                    anchor_page=None,
                    print_order="",
                    excluded_pages="",
                    page="Todas",
                    last_output=None,
                    job_log=[],
                    client=self.client.get(),
                    group_name=self.group_name.get(),
                    crops={},
                    free_crops={},
                    copies=1,
                    content_pct=100,
                    autorotate=True,
                    nup_center=True,
                )
                self.tabs_data[tid] = state
                opened.append(tid)
            except Exception as e:
                if doc is not None and not doc.is_closed:
                    doc.close()
                errors.append(f"{Path(p).name}: {e}")
        if opened:
            self.tabs.select(opened[-1])
            self.on_tab_changed()
            self.update_tab_colors()
        if errors:
            messagebox.showwarning(
                "Algunos archivos no se abrieron", "\n".join(errors[:12])
            )

    def convert_single(self, paths):
        if not paths:
            return
        for p in paths:
            try:
                with tempfile.TemporaryDirectory(prefix="grafiplot_convert_") as tmp:
                    if Path(p).suffix.lower() in ARCHIVES:
                        extracted = unpack_archive(p, Path(tmp) / "extraidos")
                        if not extracted:
                            raise ValueError(
                                "No se encontraron archivos compatibles en el comprimido."
                            )
                        if len(extracted) > 1:
                            # Display all extracted items for the user to organize or choose.
                            self.combine_files([p])
                            continue
                        p = extracted[0]
                    source = make_pdf(str(p), tmp)
                    dest = combined_destination([p]).with_name(
                        "GRAFIPLOT_CONVERTIDO_" + uuid.uuid4().hex[:8] + ".pdf"
                    )
                    with fitz.open(source) as d:
                        d.save(str(dest), garbage=4, deflate=True)
                self.open_paths([str(dest)])
            except Exception as exc:
                messagebox.showerror("Convertir a PDF", str(exc))

    def close(self):
        # Cancel idle and delayed callbacks too, including initial layout work.
        for timer in self.tk.call("after", "info"):
            self.after_cancel(timer)
        if self.active_tab in self.tabs_data:
            if self._skip_save_tab != self.active_tab:
                self.tabs_data[self.active_tab] = self._state()
            self._skip_save_tab = None
        for state in self.tabs_data.values():
            if state["document"] and not state["document"].is_closed:
                state["document"].close()
        if self.preview_doc:
            self.preview_doc.close()
        self.tmp.cleanup()
        self.destroy()
