"""Thumbnail rendering, selection and non-destructive page edits."""

import os
import tkinter as tk
import uuid
from tkinter import messagebox, ttk

import pymupdf as fitz
from PIL import Image, ImageTk

from grafiplot.core.pages import parse_excluded_pages, parse_page_order
from grafiplot.core.selection import selected_pdf


class PagesMixin:
    def ordered_page_ids(self):
        if not self.document:
            return []
        spec = self.print_order.get().strip()
        omitted = parse_excluded_pages(self.excluded_pages.get(), len(self.document))
        if spec:
            return [
                n
                for n in parse_page_order(spec, len(self.document))
                if n not in omitted
            ]
        if self.page.get() == "Todas":
            return [n for n in range(len(self.document)) if n not in omitted]
        if self.page.get() == "Selección de miniaturas":
            if not self.selected_pages:
                raise ValueError(
                    "Seleccione miniaturas o cambie a Todas para imprimir todo el documento."
                )
            return sorted(self.selected_pages - omitted)
        num = int(self.page.get())
        if not 1 <= num <= len(self.document):
            raise ValueError("Página fuera del documento.")
        return [] if num - 1 in omitted else [num - 1]

    def select_all(self):
        if self.document:
            self.page.set("Todas")
            self.selected_pages = set(range(len(self.document)))
            self.refresh_selection()
            self.invalidate_preview()

    def clear_selection(self):
        self.selected_pages.clear()
        self.page.set("Todas")
        self.refresh_selection()
        self.invalidate_preview()

    def mark_printed(self):
        if not self.selected_pages:
            return messagebox.showinfo(
                "Selección", "Seleccione páginas antes de marcarlas."
            )
        self.sent_pages.update(self.selected_pages)
        self.refresh_selection()

    def refresh_selection(self):
        for i, btn in self.thumbnail_buttons.items():
            selected = i in self.selected_pages
            sent = i in self.sent_pages
            bg = "#d7f0e3" if sent else ("#f8e3e7" if selected else "#ffffff")
            btn.configure(
                bg=bg,
                activebackground=bg,
                relief="flat",
                bd=1,
                highlightthickness=2 if selected else 1,
                highlightbackground=(
                    "#b51f38" if selected else ("#63aa85" if sent else "#dce1e8")
                ),
            )
        if hasattr(self, "selected_label"):
            self.selected_label.configure(
                text=f"{len(self.selected_pages)} seleccionadas · {len(self.sent_pages)} enviadas"
            )

    def selected_source(self):
        ids = self.ordered_page_ids()
        subset = os.path.join(self.tmp.name, "paginas_en_orden.pdf")
        selected_pdf(self.document, ids, subset, self.crops, self.free_crops)
        args = list(self.params())
        args[7] = -1  # All pages in the independent working PDF.
        return subset, tuple(args), set(ids)

    def _thumbnail_canvas_resize(self, event):
        self.thumb_canvas.itemconfigure(
            self.thumb_window, width=max(90, event.width - 6)
        )
        if getattr(self, "_thumb_last_width", None) != event.width:
            self._thumb_last_width = event.width
            if self.document:
                self.schedule_thumbnails()

    def schedule_thumbnails(self):
        if self._thumbnail_timer is not None:
            self.after_cancel(self._thumbnail_timer)
        self._thumbnail_timer = self.after(100, self._update_scheduled_thumbnails)

    def _update_scheduled_thumbnails(self):
        self._thumbnail_timer = None
        self.update_thumbnails()

    def update_thumbnails(self):
        """Create lightweight placeholders and render thumbnails in small UI batches."""
        if not hasattr(self, "thumb_frame"):
            return
        self._thumb_generation += 1
        self._preview_cache.clear()
        self._preview_cache_bytes = 0
        generation = self._thumb_generation
        if self._thumb_after is not None:
            try:
                self.after_cancel(self._thumb_after)
            except Exception:
                pass
            self._thumb_after = None
        for child in self.thumb_frame.winfo_children():
            child.destroy()
        self.thumbnails = []
        self.thumbnail_buttons = {}
        self._thumb_images = {}
        if not self.document:
            return
        size = self.thumb_size.get()
        available = max(90, self.thumb_canvas.winfo_width() - 12)
        columns = max(1, available // max(60, size))
        total = min(len(self.document), 500)
        for i in range(total):
            btn = tk.Button(
                self.thumb_frame,
                text=str(i + 1),
                width=max(5, size // 13),
                height=max(3, size // 30),
                bg="#eeeeee",
                fg="#111111",
                activebackground="#ffb2b2",
                bd=1,
                highlightthickness=0,
                command=lambda n=i: self.select_thumbnail(n),
            )
            btn.grid(row=i // columns, column=i % columns, padx=2, pady=3, sticky="n")
            self.thumbnail_buttons[i] = btn
            btn.bind(
                "<Control-Button-1>", lambda e, n=i: self.select_thumbnail(n, "toggle")
            )
            btn.bind(
                "<Shift-Button-1>", lambda e, n=i: self.select_thumbnail(n, "range")
            )
            btn.bind("<MouseWheel>", self.wheel_thumbnails)
            btn.bind("<Button-3>", lambda e, n=i: self.show_thumbnail_menu(e, n))
        if len(self.document) > 500:
            tk.Label(
                self.thumb_frame,
                text="Primeras 500 páginas",
                bg="#eeeeee",
                fg="#111111",
            ).grid()
        self.refresh_selection()
        self._thumb_after = self.after(
            10, lambda: self._render_thumbnail_batch(generation, 0, total, size)
        )

    def _render_thumbnail_batch(self, generation, index, total, size):
        if generation != self._thumb_generation or not self.document:
            return
        for i in range(index, min(index + 6, total)):
            try:
                pg = self.document[i]
                visible = (
                    (fitz.Rect(self.crops[i]) & pg.rect) if i in self.crops else pg.rect
                )
                if visible.is_empty:
                    visible = pg.rect
                key = (id(self.document), i, size, tuple(round(x, 3) for x in visible))
                cached = self._thumb_cache.get(key)
                if cached is None:
                    factor = min(
                        (size - 12) / visible.width, (size * 1.35) / visible.height
                    )
                    pix = pg.get_pixmap(
                        matrix=fitz.Matrix(factor, factor), clip=visible, alpha=False
                    )
                    cached = (pix.width, pix.height, bytes(pix.samples))
                    self._thumb_cache[key] = cached
                    while len(self._thumb_cache) > self._thumb_cache_limit:
                        self._thumb_cache.popitem(last=False)
                else:
                    self._thumb_cache.move_to_end(key)
                img = Image.frombytes("RGB", (cached[0], cached[1]), cached[2])
                tkimg = ImageTk.PhotoImage(img)
                self._thumb_images[i] = tkimg
                btn = self.thumbnail_buttons.get(i)
                if btn and btn.winfo_exists():
                    btn.configure(image=tkimg, compound="top", width=0, height=0)
            except Exception:
                continue
        if index + 6 < total:
            self._thumb_after = self.after(
                4,
                lambda: self._render_thumbnail_batch(
                    generation, index + 6, total, size
                ),
            )
        else:
            self._thumb_after = None

    def show_thumbnail_menu(self, event, n):
        # Right click preserves an existing multi-selection if the clicked page is included.
        if n not in self.selected_pages:
            self.select_thumbnail(n)
        menu = tk.Menu(self, tearoff=0)
        menu.add_command(
            label="Girar 90° a la derecha",
            command=lambda: self.rotate_selected_pages(90),
        )
        menu.add_command(
            label="Girar 90° a la izquierda",
            command=lambda: self.rotate_selected_pages(-90),
        )
        menu.add_separator()
        menu.add_command(
            label="Eliminar páginas seleccionadas (Supr)",
            command=self.delete_selected_pages,
        )
        menu.add_command(label="Recortar sección con mouse", command=self.start_crop)
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()
        return "break"

    def _save_edit(self, new_doc, old_indices):
        """Commit edited pages to an independent PDF and remap per-page state."""

        target = os.path.join(self.tmp.name, "editado_" + uuid.uuid4().hex + ".pdf")
        new_doc.save(target, garbage=3, deflate=True)
        new_doc.close()
        previous = self.document
        self.document = fitz.open(target)
        self.source = target
        if previous:
            previous.close()
        mapping = {old: new for new, old in enumerate(old_indices)}
        self.crops = {mapping[k]: v for k, v in self.crops.items() if k in mapping}
        self.free_crops = {
            mapping[k]: v for k, v in self.free_crops.items() if k in mapping
        }
        self.sent_pages = {mapping[k] for k in self.sent_pages if k in mapping}
        self.last_export_pages = set()
        self.selected_pages = set()
        self.anchor_page = None
        self.excluded_pages.set("")
        self.print_order.set("")
        self.page.set("Todas")
        self.update_thumbnails()
        self.invalidate_preview()
        if self.active_tab in self.tabs_data:
            if self._skip_save_tab != self.active_tab:
                self.tabs_data[self.active_tab] = self._state()
            self._skip_save_tab = None

    def delete_selected_pages(self, event=None):
        # Ignore Delete while typing in a text entry.
        if event is not None and isinstance(
            event.widget, (tk.Entry, ttk.Entry, tk.Text, ttk.Combobox)
        ):
            return
        if not self.document or not self.selected_pages:
            return
        ids = sorted(self.selected_pages)
        if len(ids) == len(self.document):
            messagebox.showwarning(
                "Eliminar páginas", "No se puede dejar el documento sin páginas."
            )
            return "break"
        if not messagebox.askyesno(
            "Eliminar páginas",
            f"¿Quitar {len(ids)} página(s) de esta pestaña?\nEl archivo original no se modificará.",
        ):
            return "break"
        keep = [i for i in range(len(self.document)) if i not in self.selected_pages]
        edited = fitz.open()
        for n in keep:
            edited.insert_pdf(self.document, from_page=n, to_page=n)
        self._save_edit(edited, keep)
        return "break"

    def rotate_selected_pages(self, degrees):
        if not self.document or not self.selected_pages:
            return
        edited = fitz.open()
        edited.insert_pdf(self.document)
        for n in self.selected_pages:
            edited[n].set_rotation((edited[n].rotation + degrees) % 360)
        count = len(self.selected_pages)
        self._save_edit(edited, list(range(len(self.document))))
        self.preview_status.configure(
            text=f"{count} página(s) girada(s); documento original intacto."
        )

    def select_thumbnail(self, n, action="single"):
        if action == "toggle":
            if n in self.selected_pages:
                self.selected_pages.remove(n)
            else:
                self.selected_pages.add(n)
        elif action == "range" and self.anchor_page is not None:
            self.selected_pages.update(
                range(min(n, self.anchor_page), max(n, self.anchor_page) + 1)
            )
        else:
            self.selected_pages = {n}
        self.anchor_page = n
        self.page.set("Selección de miniaturas")
        self.refresh_selection()
        self.invalidate_preview()
        return "break"

    def exclude_pages_dialog(self):
        if not self.document:
            return messagebox.showinfo("Excluir páginas", "Abra un documento primero.")
        dialog = tk.Toplevel(self)
        dialog.title("Excluir páginas SOLO de la impresión")
        dialog.geometry("510x190")
        dialog.transient(self)
        dialog.grab_set()
        ttk.Label(
            dialog,
            text=f"Páginas que NO se imprimirán (1 a {len(self.document)}):",
            font=("Segoe UI", 11, "bold"),
        ).pack(anchor="w", padx=14, pady=(14, 5))
        entry = ttk.Entry(dialog, textvariable=self.excluded_pages)
        entry.pack(fill="x", padx=14)
        entry.focus_set()
        ttk.Label(
            dialog, text="Ejemplo: 2,4,7-10. El PDF original nunca se altera."
        ).pack(anchor="w", padx=14, pady=8)

        def save():
            try:
                parse_excluded_pages(self.excluded_pages.get(), len(self.document))
            except Exception as e:
                return messagebox.showerror("Páginas inválidas", str(e), parent=dialog)
            dialog.destroy()
            self.invalidate_preview()

        ttk.Button(dialog, text="APLICAR EXCLUSIÓN", command=save).pack(pady=8)
