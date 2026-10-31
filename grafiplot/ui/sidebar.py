"""Scrollable print settings with mode-specific sections."""

import tkinter as tk
from tkinter import ttk

from grafiplot.constants import PAPERS
from grafiplot.ui.theme import COLORS


def section(parent, text):
    ttk.Separator(parent).pack(fill="x", pady=(14, 10))
    ttk.Label(parent, text=text, style="Section.TLabel").pack(anchor="w", pady=(0, 2))


def build_sidebar(app, parent):
    panel = ttk.Frame(parent, style="Panel.TFrame")
    panel.pack(side="left", fill="y", padx=(0, 10))
    outer = tk.Canvas(panel, width=262, highlightthickness=0, bg=COLORS["surface"])
    scroll = ttk.Scrollbar(panel, orient="vertical", command=outer.yview)
    outer.configure(yscrollcommand=scroll.set)
    scroll.pack(side="right", fill="y")
    outer.pack(side="left", fill="both", expand=True)
    left = ttk.Frame(outer, style="Panel.TFrame", padding=(14, 14))
    win = outer.create_window((0, 0), window=left, anchor="nw", width=262)
    left.bind("<Configure>", lambda e: outer.configure(scrollregion=outer.bbox("all")))
    outer.bind("<Configure>", lambda e: outer.itemconfigure(win, width=e.width))
    app.settings_canvas = outer
    ttk.Label(left, text="Ajustes de impresión", style="Heading.TLabel").pack(
        anchor="w"
    )
    ttk.Label(left, text="Configura el resultado en papel.", style="Muted.TLabel").pack(
        anchor="w", pady=(2, 6)
    )
    app._field(
        left,
        "Modo de impresión",
        app.mode,
        ["Normal", "Póster", "Folleto", "Varias páginas por hoja"],
    )
    app.mode_options = ttk.Frame(left, style="Panel.TFrame")
    app.mode_options.pack(fill="x")
    app.poster_options = ttk.Frame(app.mode_options, style="Panel.TFrame")
    app.poster_control = app._field(
        app.poster_options,
        "Mosaico de póster",
        app.grid_type,
        [
            "4 hojas (2 × 2)",
            "6 hojas (3 × 2)",
            "8 hojas (4 × 2)",
            "9 hojas (3 × 3)",
            "Personalizado",
        ],
    )
    line = ttk.Frame(app.poster_options, style="Panel.TFrame")
    line.pack(fill="x")
    app.poster_entries = [
        app._entry(line, "Columnas", app.cols, "left"),
        app._entry(line, "Filas", app.rows, "left"),
    ]
    app.nup_options = ttk.Frame(app.mode_options, style="Panel.TFrame")
    app.nup_layout_control = app._field(
        app.nup_options,
        "Distribución",
        app.nup_layout,
        [
            "Automática",
            "Elegir columnas × filas",
            "Todas en una hoja",
            "A medida (mm, separación 5 mm)",
        ],
    )
    app.nup_auto_frame = ttk.Frame(app.nup_options, style="Panel.TFrame")
    app.nup_control = app._field(
        app.nup_auto_frame,
        "Páginas por hoja",
        app.per_sheet,
        [str(i) for i in range(1, 17)],
    )
    app.nup_grid_frame = ttk.Frame(app.nup_options, style="Panel.TFrame")
    app.nup_grid_entries = [
        app._entry(app.nup_grid_frame, "Columnas", app.nup_cols, "left"),
        app._entry(app.nup_grid_frame, "Filas", app.nup_rows, "left"),
    ]
    app.nup_measure_frame = ttk.Frame(app.nup_options, style="Panel.TFrame")
    measures = ttk.Frame(app.nup_measure_frame, style="Panel.TFrame")
    measures.pack(fill="x")
    app.nup_measure_entries = [
        app._entry(measures, "Ancho (mm)", app.nup_width, "left"),
        app._entry(measures, "Alto (mm)", app.nup_height, "left"),
    ]
    ttk.Label(
        app.nup_measure_frame,
        text="Separación de 5 mm entre páginas.",
        style="Muted.TLabel",
    ).pack(anchor="w", pady=(5, 0))
    ttk.Checkbutton(
        app.nup_measure_frame,
        text="Centrar en la hoja",
        variable=app.nup_center,
        command=app.invalidate_preview,
    ).pack(anchor="w")
    section(left, "PAPEL Y ORIENTACIÓN")
    app._field(left, "Formato del papel", app.paper, list(PAPERS))
    app.custom_dims = ttk.Frame(left, style="Panel.TFrame")
    app._entry(app.custom_dims, "Ancho (mm)", app.cw, "left")
    app._entry(app.custom_dims, "Alto (mm)", app.ch, "left")
    app.orientation_label = ttk.Label(left, text="Orientación")
    app.orientation_label.pack(anchor="w", pady=(7, 2))
    ttk.Combobox(
        left,
        textvariable=app.orientation,
        values=["Vertical", "Horizontal"],
        state="readonly",
    ).pack(fill="x")
    margins = ttk.Frame(left, style="Panel.TFrame")
    margins.pack(fill="x")
    app._entry(margins, "Margen (mm)", app.margin, "left")
    app.overlap_entry = app._entry(margins, "Solape (mm)", app.overlap, "left")
    section(left, "PÁGINAS Y ESCALA")
    app._field(
        left, "Páginas para imprimir", app.page, ["Todas", "Selección de miniaturas"]
    )
    ttk.Label(left, text="Orden personalizado").pack(anchor="w", pady=(7, 2))
    ttk.Entry(left, textvariable=app.print_order).pack(fill="x")
    ttk.Label(left, text="Ejemplo: 1, 1, 3, 5-8", style="Muted.TLabel").pack(
        anchor="w", pady=(3, 0)
    )
    app._field(
        left,
        "Ajuste a la hoja",
        app.scale,
        ["Ajustar", "Tamaño real (100%)", "Estirar para llenar (deformar)"],
    )
    row = ttk.Frame(left, style="Panel.TFrame")
    row.pack(fill="x", pady=(8, 4))
    ttk.Label(row, text="Contenido (%)").pack(side="left")
    ttk.Spinbox(
        row, from_=25, to=200, increment=5, textvariable=app.content_pct, width=6
    ).pack(side="right")
    ttk.Checkbutton(
        left,
        text="Autorrotar para aprovechar papel",
        variable=app.autorotate,
        command=app.invalidate_preview,
    ).pack(anchor="w")
    ttk.Button(
        left,
        text="Excluir páginas…",
        command=app.exclude_pages_dialog,
        style="Compact.TButton",
    ).pack(fill="x", pady=(5, 0))
    section(left, "IMPRESORA Y REPORTES")
    ttk.Checkbutton(
        left,
        text="Mostrar precio estimado",
        variable=app.book_price,
        command=app.refresh_price,
    ).pack(anchor="w")
    ttk.Button(
        left,
        text="Asignar impresora a este papel",
        command=app.assign_printer,
        style="Compact.TButton",
    ).pack(fill="x", pady=4)
    app.more_toggle = ttk.Button(
        left,
        text="Opciones de reporte  ▾",
        command=app.toggle_more_settings,
        style="Compact.TButton",
    )
    app.more_toggle.pack(fill="x", pady=4)
    app.more_settings = ttk.Frame(left, style="Panel.TFrame")
    app._field(
        app.more_settings,
        "Impresora de reporte A4",
        app.report_printer,
        ["Impresora predeterminada"],
    )
    ttk.Button(
        app.more_settings,
        text="Guardar impresora de reporte",
        command=app.save_report_printer,
        style="Compact.TButton",
    ).pack(fill="x", pady=5)
    app.more_shown = False
