"""Debounced output preparation, raster cache and preview navigation."""

import os
from tkinter import messagebox, ttk

import pymupdf as fitz
from PIL import Image, ImageTk

from grafiplot.core.layout import create_output
from grafiplot.ui.theme import COLORS


class PreviewMixin:
    def change_zoom(self, multiplier):
        self.zoom = max(0.25, min(6, self.zoom * multiplier))
        self.preview()

    def fit_zoom(self):
        self.zoom = 1.0
        self.preview()

    def wheel(self, event):
        direction = -1 if event.delta > 0 else 1
        if event.state & 0x4:
            self.change_zoom(1.15 if direction < 0 else 1 / 1.15)
        elif event.state & 0x1:
            self.canvas.xview_scroll(direction * 3, "units")
        else:
            before = self.canvas.yview()
            self.canvas.yview_scroll(direction * 4, "units")
            after = self.canvas.yview()
            if before == after:
                self.step_preview(direction)
        return "break"

    def focus_preview(self, event):
        self.canvas.focus_set()

    def key_preview(self, delta):
        self.step_preview(delta)
        return "break"

    def wheel_thumbnails(self, event):
        step = -1 if event.delta > 0 else 1
        self.thumb_canvas.yview_scroll(step * 3, "units")
        return "break"

    def invalidate_preview(self):
        if self.switching_tabs:
            return
        if self.preview_doc:
            self.preview_doc.close()
            self.preview_doc = None
        self.prepared_preview = None
        self.preview_page.set(1)
        self.last_output = None
        self.last_export_pages = set()
        self.refresh_price()
        if hasattr(self, "preview_status"):
            self.preview_status.configure(
                text=(
                    "Vista del original · Preparando resultado…"
                    if self.source
                    else "Abre un archivo y prepara su vista de impresión."
                )
            )
        self.preview()
        if not self.switching_tabs and self.source:
            self.schedule_preview()

    def schedule_preview(self):
        if self._preview_timer is not None:
            self.after_cancel(self._preview_timer)
        self._preview_timer = self.after(550, self.auto_preview)

    def auto_preview(self):
        self._preview_timer = None
        if not self.source or getattr(self, "_crop_mode", False):
            return
        try:
            self.prepare_preview(silent=True)
        except Exception:
            pass

    def step_preview(self, delta):
        if self.preview_doc:
            self.preview_page.set(
                max(1, min(len(self.preview_doc), self.preview_page.get() + delta))
            )
        elif self.document:
            self.source_preview_page = max(
                0, min(len(self.document) - 1, self.source_preview_page + delta)
            )
        self.preview()

    def prepare_preview(self, silent=False):
        if self._preview_timer is not None:
            self.after_cancel(self._preview_timer)
            self._preview_timer = None
        if not self.source:
            return messagebox.showwarning("Vista previa", "Primero abra un documento.")
        try:
            args = self.params()
            output = os.path.join(self.tmp.name, "vista_previa_salida.pdf")
            if self.preview_doc:
                self.preview_doc.close()
                self.preview_doc = None
            job_source, args, _ = self.selected_source()
            count = create_output(job_source, output, *args)
            self.preview_doc = fitz.open(output)
            self.prepared_preview = output
            self.preview_page.set(1)
            self.preview_status.configure(
                text=f"VISTA REAL • Cara 1 de {count} • flechas ◀ ▶ para recorrer • zoom disponible"
            )
            self.refresh_price(count)
            self.preview()
        except Exception as e:
            message = str(e)
            self.prepared_preview = None
            if self.preview_doc:
                try:
                    self.preview_doc.close()
                except Exception:
                    pass
                self.preview_doc = None
            self.preview_status.configure(
                text="Vista previa final no disponible: "
                + message[:140]
                + " • mostrando documento original"
            )
            self.preview()
            if not silent:
                messagebox.showerror("Vista previa", message)

    def preview(self):
        if not hasattr(self, "canvas"):
            return
        c = self.canvas
        c.delete("all")
        self._view_image_box = None
        if hasattr(self, "_empty_button"):
            self._empty_button.destroy()
            del self._empty_button
        w = max(c.winfo_width(), 300)
        h = max(c.winfo_height(), 250)
        if not self.document:
            c.configure(scrollregion=(0, 0, w, h))
            c.xview_moveto(0)
            c.yview_moveto(0)
            cy = max(90, h / 2 - 65)
            c.create_rectangle(
                w / 2 - 25,
                cy - 50,
                w / 2 + 25,
                cy + 14,
                fill="white",
                outline="#bac3d0",
                width=2,
            )
            for offset, length in [(0, 28), (10, 28), (20, 18)]:
                c.create_line(
                    w / 2 - 14,
                    cy - 28 + offset,
                    w / 2 - 14 + length,
                    cy - 28 + offset,
                    fill="#bac3d0",
                    width=2,
                )
            c.create_text(
                w / 2,
                cy + 50,
                text="Tu próxima impresión empieza aquí",
                fill=COLORS["text"],
                font=("Segoe UI", 16, "bold"),
                width=w - 40,
                justify="center",
            )
            c.create_text(
                w / 2,
                cy + 88,
                text="Abre PDF, imágenes o documentos de Office.\nOrganiza páginas y revisa el resultado antes de imprimir.",
                fill=COLORS["muted"],
                font=("Segoe UI", 10),
                width=w - 40,
                justify="center",
            )
            self._empty_button = ttk.Button(
                c,
                text="+  Abrir archivos",
                command=self.open_file,
                style="Primary.TButton",
            )
            c.create_window(w / 2, cy + 140, window=self._empty_button)
            self.info.configure(
                text="PDF, imágenes y documentos · Los originales permanecen intactos."
            )
            return
        try:
            (
                mode,
                cols,
                rows,
                paper,
                land,
                margin,
                overlap,
                pno,
                scale,
                nup,
                content_pct,
                autorotate,
                nup_center,
            ) = self.params()
            if pno == -1:
                pno = self.source_preview_page
            if self.preview_doc and not (mode == "Póster" and self.poster_whole.get()):
                pno = max(
                    0, min(len(self.preview_doc) - 1, self.preview_page.get() - 1)
                )
                page = self.preview_doc[pno]
            else:
                pno = max(0, min(len(self.document) - 1, pno))
                page = self.document[pno]
            display_rect = page.rect
            if not self.preview_doc and pno in self.crops:
                clipped = fitz.Rect(self.crops[pno]) & page.rect
                if not clipped.is_empty:
                    display_rect = clipped
            limit = min(
                3.0,
                max(
                    1.0,
                    (max(w, h) * self.zoom * 1.8)
                    / max(display_rect.width, display_rect.height),
                ),
            )
            # Reuse rasterized pages while navigating; cached bitmaps are bounded by RAM.
            key = (
                id(self.preview_doc) if self.preview_doc else id(self.document),
                pno,
                round(limit, 3),
                tuple(round(v, 2) for v in display_rect),
            )
            cached = self._preview_cache.get(key)
            if cached is None:
                try:
                    pix = page.get_pixmap(
                        matrix=fitz.Matrix(limit, limit),
                        clip=display_rect,
                        alpha=False,
                        colorspace=fitz.csRGB,
                    )
                except (RuntimeError, MemoryError, ValueError):
                    # Algunos PDF complejos o con imágenes enormes fallan al renderizar
                    # a resolución alta. Reintentar con escala reducida.
                    fallback_scale = min(1.0, limit)
                    pix = page.get_pixmap(
                        matrix=fitz.Matrix(fallback_scale, fallback_scale),
                        clip=display_rect,
                        alpha=False,
                        colorspace=fitz.csRGB,
                        annots=False,
                    )
                cached = (pix.width, pix.height, bytes(pix.samples))
                cost = len(cached[2])
                self._preview_cache[key] = cached
                self._preview_cache_bytes += cost
                while (
                    self._preview_cache_bytes > self._preview_cache_limit
                    and len(self._preview_cache) > 1
                ):
                    _, victim = self._preview_cache.popitem(last=False)
                    self._preview_cache_bytes -= len(victim[2])
            else:
                self._preview_cache.move_to_end(key)
            im = Image.frombytes("RGB", (cached[0], cached[1]), cached[2])
            factor = min((w - 55) / im.width, (h - 75) / im.height) * self.zoom
            sz = (max(1, int(im.width * factor)), max(1, int(im.height * factor)))
            im = im.resize(sz, Image.Resampling.LANCZOS)
            self.photo = ImageTk.PhotoImage(im)
            x = max(20, (w - sz[0]) / 2)
            y = max(20, (h - sz[1]) / 2)
            self._view_image_box = (x, y, x + sz[0], y + sz[1], pno, display_rect)
            c.configure(
                scrollregion=(0, 0, max(w, x + sz[0] + 22), max(h, y + sz[1] + 22))
            )
            c.create_rectangle(
                x - 3,
                y - 3,
                x + sz[0] + 3,
                y + sz[1] + 3,
                fill="white",
                outline="#8093ad",
            )
            c.create_image(x, y, anchor="nw", image=self.photo)
            if mode == "Póster" and (not self.preview_doc or self.poster_whole.get()):
                # grid displays tile boundaries as conceptual layout; physical size is calculated on export
                for j in range(1, cols):
                    xx = x + sz[0] * j / cols
                    c.create_line(
                        xx, y, xx, y + sz[1], fill="#ec3737", width=2, dash=(7, 4)
                    )
                for j in range(1, rows):
                    yy = y + sz[1] * j / rows
                    c.create_line(
                        x, yy, x + sz[0], yy, fill="#ec3737", width=2, dash=(7, 4)
                    )
                for j in range(rows):
                    for i in range(cols):
                        c.create_text(
                            x + (i + 0.5) * sz[0] / cols,
                            y + (j + 0.5) * sz[1] / rows,
                            text=str(j * cols + i + 1),
                            fill="#e11d48",
                            font=("Segoe UI", 13, "bold"),
                        )
            sheets = (
                "cuadernillo a doble cara"
                if mode == "Folleto"
                else (
                    (
                        "TODAS"
                        if isinstance(nup, tuple) and nup[0] == "all"
                        else (
                            "A MEDIDA"
                            if isinstance(nup, tuple)
                            else str(
                                ((nup - 1000) // 100) * ((nup - 1000) % 100)
                                if nup >= 1000
                                else nup
                            )
                        )
                    )
                    + " páginas EN 1 hoja"
                    if mode == "Varias páginas por hoja"
                    else str(cols * rows) + " hoja(s) por página"
                )
            )
            self.refresh_price(len(self.preview_doc) if self.preview_doc else None)
            self.info.configure(
                text=f"{mode} • {sheets} • {paper[0]:g} × {paper[1]:g} mm"
                + (
                    f" • SALIDA {pno+1}/{len(self.preview_doc)}"
                    if self.preview_doc
                    else f" • ORIGINAL {pno+1}/{len(self.document)}"
                )
            )
        except Exception as e:
            self.info.configure(text="Error en vista previa: " + str(e))
            c.create_text(
                w / 2,
                h / 2,
                text="NO SE PUDO MOSTRAR LA VISTA PREVIA\n" + str(e)[:110],
                fill="#a30e20",
                font=("Segoe UI", 12, "bold"),
                justify="center",
                width=w - 30,
            )
