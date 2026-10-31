"""Resizable page navigator and document preview panels."""

import tkinter as tk
from tkinter import ttk

from grafiplot.ui.theme import COLORS


def build_workspace(app, parent):
    app.middle = tk.PanedWindow(
        parent,
        orient="horizontal",
        sashwidth=8,
        sashrelief="flat",
        bg=COLORS["background"],
        bd=0,
    )
    app.middle.pack(side="left", fill="both", expand=True)
    thumbs = ttk.Frame(app.middle, style="Panel.TFrame", padding=12)
    app.middle.add(thumbs, minsize=154, width=196, stretch="never")
    ttk.Label(thumbs, text="Páginas", style="Heading.TLabel").pack(anchor="w")
    ttk.Label(thumbs, text="Tamaño de miniaturas", style="Muted.TLabel").pack(
        anchor="w", pady=(8, 0)
    )
    ttk.Scale(
        thumbs,
        from_=65,
        to=160,
        variable=app.thumb_size,
        command=lambda _: app.schedule_thumbnails(),
    ).pack(fill="x", pady=(0, 6))
    row = ttk.Frame(thumbs, style="Panel.TFrame")
    row.pack(fill="x")
    ttk.Button(row, text="Todas", command=app.select_all, style="Compact.TButton").pack(
        side="left", fill="x", expand=True, padx=(0, 4)
    )
    ttk.Button(
        row, text="Limpiar", command=app.clear_selection, style="Compact.TButton"
    ).pack(side="left", fill="x", expand=True)
    app.selected_label = ttk.Label(
        thumbs,
        text="0 seleccionadas · 0 enviadas",
        style="Muted.TLabel",
        wraplength=160,
    )
    app.selected_label.pack(anchor="w", pady=(8, 6))
    holder = ttk.Frame(thumbs, style="Panel.TFrame")
    holder.pack(fill="both", expand=True)
    app.thumb_canvas = tk.Canvas(
        holder, bg=COLORS["soft"], highlightthickness=0, width=145
    )
    scrollbar = ttk.Scrollbar(holder, orient="vertical", command=app.thumb_canvas.yview)
    app.thumb_canvas.configure(yscrollcommand=scrollbar.set)
    app.thumb_canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")
    app.thumb_frame = tk.Frame(app.thumb_canvas, bg=COLORS["soft"])
    app.thumb_window = app.thumb_canvas.create_window(
        (0, 0), window=app.thumb_frame, anchor="nw"
    )
    app.thumb_canvas.bind("<Configure>", app._thumbnail_canvas_resize)
    app.thumb_frame.bind(
        "<Configure>",
        lambda e: app.thumb_canvas.configure(scrollregion=app.thumb_canvas.bbox("all")),
    )
    app.thumb_canvas.bind("<MouseWheel>", app.wheel_thumbnails)
    app.thumb_frame.bind("<MouseWheel>", app.wheel_thumbnails)
    ttk.Label(
        thumbs,
        text="Ctrl+clic: varias\nShift+clic: rango · Supr: quitar\nVerde: enviado a impresión",
        style="Muted.TLabel",
        wraplength=160,
    ).pack(anchor="w", pady=(10, 6))
    ttk.Button(
        thumbs,
        text="Marcar como impresas",
        command=app.mark_printed,
        style="Compact.TButton",
    ).pack(fill="x")
    right = ttk.Frame(app.middle, style="Panel.TFrame", padding=(16, 12))
    app.middle.add(right, minsize=380, stretch="always")
    top = ttk.Frame(right, style="Panel.TFrame")
    top.pack(fill="x")
    ttk.Label(top, text="Vista previa", style="Heading.TLabel").pack(side="left")
    controls = ttk.Frame(top, style="Panel.TFrame")
    controls.pack(side="right")
    for text, command, width in (
        ("‹", lambda: app.step_preview(-1), 2),
        ("›", lambda: app.step_preview(1), 2),
        ("−", lambda: app.change_zoom(1 / 1.25), 2),
        ("+", lambda: app.change_zoom(1.25), 2),
        ("Ajustar", app.fit_zoom, 7),
    ):
        ttk.Button(
            controls, text=text, command=command, width=width, style="Compact.TButton"
        ).pack(side="left", padx=(4, 0))
    app.info = ttk.Label(
        right,
        text="Abre un archivo para comenzar.",
        style="Muted.TLabel",
        wraplength=700,
    )
    app.info.pack(anchor="w", pady=(5, 8))
    copies = ttk.Frame(right, style="Panel.TFrame")
    copies.pack(fill="x", pady=(0, 8))
    ttk.Label(copies, text="Copias", style="Section.TLabel").pack(
        side="left", padx=(0, 8)
    )
    ttk.Spinbox(
        copies, from_=1, to=9999, textvariable=app.copies, width=5, justify="center"
    ).pack(side="left")
    app.duplex_control = ttk.Checkbutton(
        copies, text="Doble cara", variable=app.duplex, command=app.invalidate_preview
    )
    app.duplex_control.pack(side="left", padx=(14, 0))
    app.crop_controls = ttk.Frame(copies, style="Panel.TFrame")
    app.crop_controls.pack(side="right")
    for text, command in [
        ("Recortar", app.start_crop),
        ("Quitar recorte", app.clear_crop),
    ]:
        button = ttk.Button(
            app.crop_controls, text=text, command=command, style="Compact.TButton"
        )
        button.pack(side="left", padx=(4, 0))
        app.document_actions.append(button)
    view = ttk.Frame(right, style="Panel.TFrame")
    view.pack(fill="both", expand=True)
    app.canvas = tk.Canvas(view, bg=COLORS["canvas"], highlightthickness=0)
    vs = ttk.Scrollbar(view, orient="vertical", command=app.canvas.yview)
    hs = ttk.Scrollbar(view, orient="horizontal", command=app.canvas.xview)
    app.canvas.configure(yscrollcommand=vs.set, xscrollcommand=hs.set)
    app.canvas.grid(row=0, column=0, sticky="nsew")
    vs.grid(row=0, column=1, sticky="ns")
    hs.grid(row=1, column=0, sticky="ew")
    view.columnconfigure(0, weight=1)
    view.rowconfigure(0, weight=1)
    app.canvas.bind("<Configure>", app.resize_preview)
    app.canvas.bind("<ButtonPress-1>", app.crop_press)
    app.canvas.bind("<B1-Motion>", app.crop_motion)
    app.canvas.bind("<ButtonRelease-1>", app.crop_release)
    app.canvas.bind("<Button-1>", app.focus_preview, add="+")
    app.canvas.bind("<MouseWheel>", app.wheel)
    for key, delta in [("<Up>", -1), ("<Down>", 1), ("<Prior>", -1), ("<Next>", 1)]:
        app.canvas.bind(key, lambda e, delta=delta: app.key_preview(delta))
    app.preview_status = ttk.Label(
        right,
        text="Abre un archivo y prepara su vista de impresión.",
        style="Muted.TLabel",
        wraplength=700,
    )
    app.preview_status.pack(anchor="w", pady=(8, 0))
    bottom = ttk.Frame(right, style="Panel.TFrame")
    bottom.pack(fill="x", pady=(3, 0))
    app.price_label = ttk.Label(bottom, text="", style="Price.TLabel")
    app.price_label.pack(anchor="w")
    ttk.Label(
        bottom, text="Ctrl+rueda: zoom  ·  Shift+rueda: desplazar", style="Muted.TLabel"
    ).pack(anchor="w", pady=(3, 0))
    app.poster_toggle = ttk.Checkbutton(
        bottom,
        text="Ver póster completo con líneas de corte",
        variable=app.poster_whole,
        command=app.preview,
    )
    right.bind("<Configure>", lambda e: _wrap_labels(app, e.width))


def _wrap_labels(app, width):
    for label in (app.info, app.preview_status, app.price_label):
        label.configure(wraplength=max(240, width - 32))
