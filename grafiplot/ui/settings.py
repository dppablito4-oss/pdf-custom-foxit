"""Print settings controls and validated output parameters."""

from tkinter import ttk

from grafiplot.constants import PAPERS


class SettingsMixin:
    def toggle_more_settings(self):
        self.more_shown = not self.more_shown
        if self.more_shown:
            self.more_settings.pack(fill="x", pady=2)
        else:
            self.more_settings.pack_forget()
        self.more_toggle.configure(
            text=(
                "Opciones de reporte  ▴"
                if self.more_shown
                else "Opciones de reporte  ▾"
            )
        )

    def update_mode_controls(self):
        """Activa solo los controles que afectan realmente al modo seleccionado."""
        if not hasattr(self, "nup_control"):
            return
        mode = self.mode.get()
        if self.paper.get() == "Personalizado":
            self.custom_dims.pack(fill="x", before=self.orientation_label)
        else:
            self.custom_dims.pack_forget()
        self.poster_options.pack_forget()
        self.nup_options.pack_forget()
        self.poster_toggle.pack_forget()
        if mode == "Póster":
            self.poster_options.pack(fill="x")
            self.poster_toggle.pack(anchor="w", pady=(4, 0))
        elif mode == "Varias páginas por hoja":
            self.nup_options.pack(fill="x")
        self.overlap_entry.configure(state="normal" if mode == "Póster" else "disabled")
        self.nup_auto_frame.pack_forget()
        if mode == "Varias páginas por hoja" and self.nup_layout.get() == "Automática":
            self.nup_auto_frame.pack(fill="x")
        self.nup_control.configure(
            state=(
                "readonly"
                if mode == "Varias páginas por hoja"
                and self.nup_layout.get() == "Automática"
                else "disabled"
            )
        )
        self.nup_layout_control.configure(
            state="readonly" if mode == "Varias páginas por hoja" else "disabled"
        )
        if (
            mode == "Varias páginas por hoja"
            and self.nup_layout.get() == "Elegir columnas × filas"
        ):
            self.nup_grid_frame.pack(fill="x")
        else:
            self.nup_grid_frame.pack_forget()
        if (
            mode == "Varias páginas por hoja"
            and self.nup_layout.get() == "A medida (mm, separación 5 mm)"
        ):
            self.nup_measure_frame.pack(fill="x")
        else:
            self.nup_measure_frame.pack_forget()
        self.poster_control.configure(
            state="readonly" if mode == "Póster" else "disabled"
        )
        # Entradas de columnas / filas solo se usan con póster personalizado.
        if hasattr(self, "poster_entries"):
            for entry in self.poster_entries:
                entry.configure(
                    state=(
                        "normal"
                        if mode == "Póster" and self.grid_type.get() == "Personalizado"
                        else "disabled"
                    )
                )
        if mode == "Folleto":
            self.duplex.set(True)
            self.duplex_control.state(["disabled"])
        else:
            self.duplex_control.state(["!disabled"])
        if not self.switching_tabs:
            self.invalidate_preview()

    def settings_wheel(self, event):
        """Scroll settings while pointer is over the settings panel or its controls."""
        if not hasattr(self, "settings_canvas"):
            return
        target = self.winfo_containing(event.x_root, event.y_root)
        if target is None:
            return
        widget = target
        while widget is not None:
            if widget == self.settings_canvas:
                step = (
                    -1
                    if getattr(event, "num", 0) == 4 or getattr(event, "delta", 0) > 0
                    else 1
                )
                self.settings_canvas.yview_scroll(step * 3, "units")
                return "break"
            widget = widget.master

    def _field(self, parent, label, var, options):
        ttk.Label(parent, text=label).pack(anchor="w", pady=(7, 2))
        cb = ttk.Combobox(parent, textvariable=var, values=options, state="readonly")
        cb.pack(fill="x")
        return cb

    def _entry(self, parent, label, var, side):
        group = ttk.Frame(parent, style="Panel.TFrame")
        group.pack(side=side, fill="x", expand=True, padx=(0, 9))
        ttk.Label(group, text=label).pack(anchor="w", pady=(5, 1))
        entry = ttk.Entry(group, textvariable=var, width=11)
        entry.pack(fill="x")
        return entry

    def sync_grid(self):
        preset = {
            "4 hojas (2 × 2)": (2, 2),
            "6 hojas (3 × 2)": (3, 2),
            "8 hojas (4 × 2)": (4, 2),
            "9 hojas (3 × 3)": (3, 3),
        }
        if self.grid_type.get() in preset:
            a, b = preset[self.grid_type.get()]
            self.cols.set(str(a))
            self.rows.set(str(b))

    def params(self):
        mode = self.mode.get()
        cols = int(self.cols.get()) if mode == "Póster" else 1
        rows = int(self.rows.get()) if mode == "Póster" else 1
        if not 1 <= cols <= 30 or not 1 <= rows <= 30 or cols * rows > 300:
            raise ValueError("Seleccione entre 1 y 300 hojas (máximo 30 por lado).")
        margin = float(self.margin.get().replace(",", "."))
        overlap = float(self.overlap.get().replace(",", ".")) if mode == "Póster" else 0
        if not 0 <= margin <= 100 or not 0 <= overlap <= 100:
            raise ValueError("Los márgenes y solapes deben estar entre 0 y 100 mm.")
        paper = PAPERS[self.paper.get()]
        if paper is None:
            paper = (
                float(self.cw.get().replace(",", ".")),
                float(self.ch.get().replace(",", ".")),
            )
        if not all(30 <= v <= 2000 for v in paper):
            raise ValueError("Papel personalizado: entre 30 y 2000 mm por lado.")
        pno = (
            -1
            if self.page.get() in ("Todas", "Selección de miniaturas")
            else int(self.page.get()) - 1
        )
        if self.document and pno != -1 and not 0 <= pno < len(self.document):
            raise ValueError("Número de página fuera del documento.")
        nup = int(self.per_sheet.get())
        if (
            self.mode.get() == "Varias páginas por hoja"
            and self.nup_layout.get() == "Elegir columnas × filas"
        ):
            nc, nr = int(self.nup_cols.get()), int(self.nup_rows.get())
            if nc < 1 or nr < 1 or nc > 16 or nr > 16 or nc * nr > 256:
                raise ValueError(
                    "Elija de 1 a 16 columnas y filas (máximo 256 páginas)."
                )
            nup = 1000 + nc * 100 + nr
        elif (
            self.mode.get() == "Varias páginas por hoja"
            and self.nup_layout.get() == "Todas en una hoja"
        ):
            nup = ("all",)
        elif (
            self.mode.get() == "Varias páginas por hoja"
            and self.nup_layout.get() == "A medida (mm, separación 5 mm)"
        ):
            cw = float(self.nup_width.get().replace(",", "."))
            ch = float(self.nup_height.get().replace(",", "."))
            if not 5 <= cw <= 2000 or not 5 <= ch <= 2000:
                raise ValueError("Ancho y alto: de 5 a 2000 mm.")
            nup = ("measure", cw, ch)
        content_pct = int(self.content_pct.get())
        if not 25 <= content_pct <= 200:
            raise ValueError("El tamaño del contenido debe estar entre 25 y 200 %.")
        return (
            self.mode.get(),
            cols,
            rows,
            paper,
            self.orientation.get() == "Horizontal",
            margin,
            overlap,
            pno,
            self.scale.get(),
            nup,
            content_pct,
            self.autorotate.get(),
            self.nup_center.get(),
        )
