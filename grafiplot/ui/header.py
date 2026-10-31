"""Application actions, printer bar and horizontal document navigator."""

import tkinter as tk
from tkinter import ttk

from grafiplot.ui.theme import COLORS


def build_header(app):
    header = ttk.Frame(app, style="Panel.TFrame", padding=(18, 12))
    header.pack(fill="x")
    brand = ttk.Frame(header, style="Panel.TFrame")
    brand.pack(side="left")
    ttk.Label(brand, text="GRAFIPLOT", style="Brand.TLabel").pack(anchor="w")
    ttk.Label(
        brand, text="PDF PRINT  /  Estudio de impresión", style="Muted.TLabel"
    ).pack(anchor="w")
    actions = ttk.Frame(header, style="Panel.TFrame")
    actions.pack(side="right")
    ttk.Button(
        actions,
        text="+  Abrir archivos",
        command=app.open_file,
        style="Primary.TButton",
    ).pack(side="left", padx=(0, 6))
    ttk.Button(actions, text="Combinar PDF", command=app.combine_files).pack(
        side="left", padx=(0, 6)
    )
    for text, command, style in (
        ("Guardar PDF", app.export, "TButton"),
        ("Vista previa", app.prepare_preview, "TButton"),
        ("Imprimir", app.print_file, "Dark.TButton"),
    ):
        button = ttk.Button(actions, text=text, command=command, style=style)
        button.pack(side="left", padx=(0, 6))
        app.document_actions.append(button)
    ttk.Separator(app).pack(fill="x")
    bar = ttk.Frame(app, style="Panel.TFrame", padding=(18, 10))
    bar.pack(fill="x")
    bar.columnconfigure(1, weight=1)
    ttk.Label(bar, text="Impresora", style="Section.TLabel").grid(
        row=0, column=0, padx=(0, 8)
    )
    app.top_printer_combo = ttk.Combobox(
        bar,
        textvariable=app.printer,
        values=["Impresora predeterminada"],
        state="readonly",
        width=22,
    )
    app.top_printer_combo.grid(row=0, column=1, sticky="ew", padx=(0, 6))
    ttk.Button(
        bar, text="Ajustes", command=app.printer_preferences, style="Compact.TButton"
    ).grid(row=0, column=2, padx=2)
    ttk.Button(
        bar, text="Propiedades", command=app.printer_properties, style="Compact.TButton"
    ).grid(row=0, column=3, padx=2)
    ttk.Button(
        bar, text="Actualizar", command=app.refresh_printers, style="Compact.TButton"
    ).grid(row=0, column=4, padx=(2, 16))
    ttk.Label(bar, text="Cliente / pedido", style="Section.TLabel").grid(
        row=0, column=5, padx=(0, 8)
    )
    client = ttk.Entry(bar, textvariable=app.client, width=15)
    client.grid(row=0, column=6, padx=(0, 6))
    client.bind("<FocusOut>", lambda e: app.update_tab_colors())
    client.bind("<Return>", lambda e: app.update_tab_colors())
    ttk.Button(
        bar, text="Grupos", command=app.manage_groups, style="Compact.TButton"
    ).grid(row=0, column=7, padx=2)
    button = ttk.Button(
        bar, text="Reporte A4", command=app.report_tab, style="Compact.TButton"
    )
    button.grid(row=0, column=8, padx=(2, 0))
    app.document_actions.append(button)


def build_document_strip(app):
    app.tabs = ttk.Notebook(app, style="GRAFI.Hidden.TNotebook")
    strip = ttk.Frame(app)
    strip.pack(fill="x", padx=16, pady=(10, 8))
    ttk.Label(strip, text="ARCHIVOS", style="Footer.TLabel").pack(
        side="left", padx=(0, 10)
    )
    ttk.Button(
        strip,
        text="‹",
        width=2,
        command=lambda: app.navigate_tabs(-1),
        style="Compact.TButton",
    ).pack(side="left", padx=(0, 3))
    app.tab_scroll_canvas = tk.Canvas(
        strip, height=36, highlightthickness=0, bg=COLORS["background"]
    )
    app.tab_scroll_canvas.pack(side="left", fill="x", expand=True)
    app.tab_scroll_frame = tk.Frame(app.tab_scroll_canvas, bg=COLORS["background"])
    app.tab_scroll_window = app.tab_scroll_canvas.create_window(
        (0, 0), window=app.tab_scroll_frame, anchor="nw"
    )
    app.tab_scroll_frame.bind(
        "<Configure>",
        lambda e: app.tab_scroll_canvas.configure(
            scrollregion=app.tab_scroll_canvas.bbox("all")
        ),
    )
    app.tab_scroll_canvas.bind("<MouseWheel>", app.scroll_tab_strip)
    app.tab_scroll_canvas.bind("<Shift-MouseWheel>", app.scroll_tab_strip)
    app.tab_scroll_canvas.bind("<Left>", lambda e: app.navigate_tabs(-1))
    app.tab_scroll_canvas.bind("<Right>", lambda e: app.navigate_tabs(1))
    ttk.Button(
        strip,
        text="›",
        width=2,
        command=lambda: app.navigate_tabs(1),
        style="Compact.TButton",
    ).pack(side="left", padx=3)
    close = ttk.Button(
        strip, text="Cerrar archivo ×", command=app.close_tab, style="Compact.TButton"
    )
    close.pack(side="right", padx=(8, 0))
    app.document_actions.append(close)
