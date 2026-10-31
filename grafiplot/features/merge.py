"""Interactive merge planner with ordering and exclusions."""

import tempfile
import tkinter as tk
import uuid
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

import pymupdf as fitz

from grafiplot.constants import ARCHIVES, SUPPORTED_MERGE
from grafiplot.core.archives import unpack_archive
from grafiplot.core.conversion import make_pdf
from grafiplot.core.merge import combine_documents
from grafiplot.core.pages import parse_excluded_pages


class MergeMixin:
    def combine_files(self, paths=None):
        """Show a reorderable merge planner before committing any output."""
        if paths is None:
            paths = filedialog.askopenfilenames(
                title="Archivos a combinar (también ZIP y RAR)",
                filetypes=[
                    (
                        "Documentos y comprimidos",
                        "*.pdf *.doc *.docx *.xls *.xlsx *.ppt *.pptx *.odt *.ods *.odp *.rtf *.txt *.png *.jpg *.jpeg *.bmp *.tif *.tiff *.webp *.gif *.zip *.rar",
                    ),
                    ("Todos", "*.*"),
                ],
            )
        if not paths:
            return
        workspace = tempfile.TemporaryDirectory(prefix="grafiplot_archivos_")

        def expand(paths_to_add):
            collected = []
            for j, raw in enumerate(paths_to_add):
                path = str(raw)
                if Path(path).suffix.lower() in ARCHIVES:
                    sub = Path(workspace.name) / (
                        "extraido_" + str(uuid.uuid4().hex[:10])
                    )
                    extracted = unpack_archive(path, sub)
                    collected.extend([[item, ""] for item in extracted])
                elif Path(path).suffix.lower() in SUPPORTED_MERGE:
                    collected.append([path, ""])
            return collected

        try:
            initial = expand(paths)
        except Exception as exc:
            workspace.cleanup()
            return messagebox.showerror("Archivos comprimidos", str(exc))
        if not initial:
            workspace.cleanup()
            return messagebox.showwarning(
                "Combinar", "No se encontraron documentos compatibles."
            )
        dialog = tk.Toplevel(self)
        dialog.title("GRAFIPLOT — Ordenar documentos antes de combinar")
        dialog.geometry("890x650")
        dialog.minsize(700, 530)
        dialog.transient(self)
        dialog.grab_set()
        items = initial
        dialog.protocol(
            "WM_DELETE_WINDOW", lambda: (workspace.cleanup(), dialog.destroy())
        )

        def close_merge():
            workspace.cleanup()
            dialog.destroy()

        ttk.Label(
            dialog,
            text="ORDEN DE COMBINACIÓN — arrastra los documentos con el mouse",
            font=("Segoe UI", 13, "bold"),
        ).pack(anchor="w", padx=15, pady=(13, 5))
        ttk.Label(
            dialog,
            text="ZIP/RAR: se descomprimen temporalmente y sus documentos aparecen abajo. Puedes reordenarlos y omitir páginas.",
        ).pack(anchor="w", padx=15)
        main = ttk.Frame(dialog)
        main.pack(fill="both", expand=True, padx=15, pady=8)
        lb = tk.Listbox(
            main, font=("Segoe UI", 11), selectmode="browse", activestyle="dotbox"
        )
        lb.pack(side="left", fill="both", expand=True)
        scroll = ttk.Scrollbar(main, command=lb.yview)
        scroll.pack(side="left", fill="y")
        lb.configure(yscrollcommand=scroll.set)
        controls = ttk.Frame(main)
        controls.pack(side="right", fill="y", padx=(10, 0))

        def render(index=0):
            lb.delete(0, "end")
            for i, (path, skip) in enumerate(items):
                lb.insert(
                    "end",
                    f"{i+1}. {Path(path).name}"
                    + (f"  [Omitir: {skip}]" if skip else ""),
                )
            if items:
                lb.selection_set(max(0, min(index, len(items) - 1)))

        # Drag and drop reorders entries within the list; keeps each document's exclusions attached.
        drag = {"start": None}

        def drag_begin(event):
            if not items:
                return
            idx = lb.nearest(event.y)
            if 0 <= idx < len(items):
                drag["start"] = idx
                lb.selection_clear(0, "end")
                lb.selection_set(idx)

        def drag_end(event):
            old = drag["start"]
            drag["start"] = None
            if old is None or not items:
                return
            new = max(0, min(lb.nearest(event.y), len(items) - 1))
            if new == old:
                return
            item = items.pop(old)
            items.insert(new, item)
            render(new)

        lb.bind("<ButtonPress-1>", drag_begin, add="+")
        lb.bind("<ButtonRelease-1>", drag_end, add="+")

        def current():
            return lb.curselection()[0] if lb.curselection() else None

        def move(step):
            i = current()
            if i is None or not (0 <= i + step < len(items)):
                return
            items[i], items[i + step] = items[i + step], items[i]
            render(i + step)

        def add():
            more = filedialog.askopenfilenames(parent=dialog, title="Agregar archivos")
            try:
                items.extend(expand(more))
            except Exception as exc:
                messagebox.showerror("Extraer archivos", str(exc), parent=dialog)
            render(len(items) - 1)

        def remove():
            i = current()
            if i is not None:
                items.pop(i)
                render(min(i, len(items) - 1))

        def omit():
            i = current()
            if i is None:
                return
            pop = tk.Toplevel(dialog)
            pop.title("Omitir páginas")
            pop.geometry("470x180")
            pop.transient(dialog)
            pop.grab_set()
            ttk.Label(
                pop,
                text=f"Páginas a excluir de {Path(items[i][0]).name}",
                wraplength=420,
            ).pack(padx=10, pady=(12, 5))
            var = tk.StringVar(value=items[i][1])
            ent = ttk.Entry(pop, textvariable=var)
            ent.pack(fill="x", padx=12)
            ent.focus_set()
            ttk.Label(pop, text="Ejemplo: 1,3,5-8. Se conservan los originales.").pack(
                pady=8
            )

            def accept():
                try:
                    with tempfile.TemporaryDirectory(prefix="grafiplot_excl_") as tmp:
                        pdf = make_pdf(items[i][0], tmp)
                        with fitz.open(pdf) as d:
                            parse_excluded_pages(var.get(), d.page_count)
                except Exception as e:
                    return messagebox.showerror("Páginas inválidas", str(e), parent=pop)
                items[i][1] = var.get().strip()
                pop.destroy()
                render(i)

            ttk.Button(pop, text="GUARDAR", command=accept).pack()

        for label, func in [
            ("SUBIR ↑", lambda: move(-1)),
            ("BAJAR ↓", lambda: move(1)),
            ("AGREGAR", add),
            ("QUITAR ARCHIVO", remove),
            ("OMITIR PÁGINAS", omit),
        ]:
            ttk.Button(controls, text=label, command=func).pack(fill="x", pady=5)
        ttk.Label(
            dialog, text="MODO DE COMBINACIÓN:", font=("Segoe UI", 10, "bold")
        ).pack(anchor="w", padx=15, pady=(5, 2))
        mode = tk.StringVar(value="simple")
        ttk.Radiobutton(
            dialog,
            text="Solo combinar — para imprimir a una cara, sin separadores ni páginas añadidas",
            variable=mode,
            value="simple",
        ).pack(anchor="w", padx=15, pady=2)
        pad_odd_always = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            dialog,
            text="Añadir 1 página blanca al FINAL de cada documento impar (también a una cara)",
            variable=pad_odd_always,
        ).pack(anchor="w", padx=35, pady=2)
        simplex_sep = tk.BooleanVar(value=False)
        simple_sep_check = ttk.Checkbutton(
            dialog,
            text="Opcional a UNA CARA: insertar 1 página separadora blanca entre documentos",
            variable=simplex_sep,
        )
        simple_sep_check.pack(anchor="w", padx=35, pady=2)
        ttk.Radiobutton(
            dialog,
            text="Para imprimir a doble cara — completar documentos impares con 1 hoja blanca y agregar 2 páginas blancas entre documentos",
            variable=mode,
            value="doble",
        ).pack(anchor="w", padx=15, pady=2)
        rotate_odd_var = tk.BooleanVar(value=False)
        rotate_checkbox = ttk.Checkbutton(
            dialog,
            text="Opcional: horizontales impares 90° izquierda y pares 90° derecha",
            variable=rotate_odd_var,
        )
        rotate_checkbox.pack(anchor="w", padx=35, pady=2)

        def sync_options(*_):
            if mode.get() == "simple":
                simple_sep_check.state(["!disabled"])
                rotate_odd_var.set(False)
                rotate_checkbox.state(["disabled"])
            else:
                simplex_sep.set(False)
                simple_sep_check.state(["disabled"])
                rotate_checkbox.state(["!disabled"])

        mode.trace_add("write", sync_options)
        sync_options()
        ttk.Label(
            dialog,
            text="Verifica el giro con 2 páginas de prueba: el controlador puede tener su propia opción de volteo.",
            wraplength=770,
        ).pack(anchor="w", padx=15, pady=(0, 3))

        def execute():
            if len(items) < 2:
                return messagebox.showerror(
                    "Combinar", "Seleccione al menos dos archivos.", parent=dialog
                )
            try:
                output, count = combine_documents(
                    [p for p, _ in items],
                    work_dir=self.tmp.name,
                    exclusions=[ex for _, ex in items],
                    duplex_mode=(mode.get() == "doble"),
                    rotate_odd_landscape=rotate_odd_var.get(),
                    simplex_separator=simplex_sep.get(),
                    pad_each_odd=pad_odd_always.get(),
                )
            except Exception as exc:
                return messagebox.showerror(
                    "Error al combinar", str(exc), parent=dialog
                )
            close_merge()
            self.open_paths([output])
            messagebox.showinfo(
                "Combinación completada",
                f"Se creó un PDF de {count} páginas y se abrió en otra pestaña.\n\n{output}\n\nOriginales intactos.",
            )

        actions = ttk.Frame(dialog)
        actions.pack(fill="x", padx=15, pady=(4, 15))
        ttk.Button(actions, text="CANCELAR", command=close_merge).pack(
            side="right", padx=5
        )
        ttk.Button(
            actions,
            text="COMBINAR Y ABRIR PDF",
            command=execute,
            style="Compact.TButton",
        ).pack(side="right", padx=5)
        render()
