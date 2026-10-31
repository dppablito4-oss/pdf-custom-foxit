"""Mouse crop operations applied to working copies."""

from tkinter import messagebox

import pymupdf as fitz


class CropMixin:
    def start_crop(self):
        if not self.document:
            return messagebox.showinfo("Recortar", "Abra un archivo primero.")
        if self.preview_doc:
            self.preview_doc.close()
            self.preview_doc = None
        self.prepared_preview = None
        if self._preview_timer is not None:
            self.after_cancel(self._preview_timer)
            self._preview_timer = None
        self._crop_mode = True
        self.canvas.configure(cursor="crosshair")
        self.preview_status.configure(
            text="RECORTE: arrastre el mouse sobre la página ORIGINAL para elegir la zona a imprimir."
        )
        self.preview()

    def crop_press(self, event):
        if not getattr(self, "_crop_mode", False) or not self._view_image_box:
            return
        x0, y0, x1, y1, _, _ = self._view_image_box
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        self._crop_anchor = (max(x0, min(x1, x)), max(y0, min(y1, y)))

    def crop_motion(self, event):
        if not self._crop_anchor or not getattr(self, "_crop_mode", False):
            return
        if self._crop_rectangle:
            self.canvas.delete(self._crop_rectangle)
        x, y = self._crop_anchor
        self._crop_rectangle = self.canvas.create_rectangle(
            x,
            y,
            self.canvas.canvasx(event.x),
            self.canvas.canvasy(event.y),
            outline="#ed1717",
            width=3,
            dash=(5, 3),
        )

    def crop_release(self, event):
        if not self._crop_anchor or not self._view_image_box:
            return
        x0, y0, x1, y1, pno, rect = self._view_image_box
        a, b = self._crop_anchor
        c = self.canvas.canvasx(event.x)
        d = self.canvas.canvasy(event.y)
        a, c = sorted([max(x0, min(x1, a)), max(x0, min(x1, c))])
        b, d = sorted([max(y0, min(y1, b)), max(y0, min(y1, d))])
        self._crop_anchor = None
        self._crop_mode = False
        self.canvas.configure(cursor="")
        if c - a < 8 or d - b < 8:
            self.preview_status.configure(
                text="Área demasiado pequeña; intente un rectángulo mayor."
            )
            return
        region = fitz.Rect(
            rect.x0 + (a - x0) / (x1 - x0) * rect.width,
            rect.y0 + (b - y0) / (y1 - y0) * rect.height,
            rect.x0 + (c - x0) / (x1 - x0) * rect.width,
            rect.y0 + (d - y0) / (y1 - y0) * rect.height,
        )
        # Mismo rectángulo relativo en todas las páginas; el recorte persiste al navegar.
        original = self.document[pno].rect
        fx0 = (region.x0 - original.x0) / original.width
        fy0 = (region.y0 - original.y0) / original.height
        fx1 = (region.x1 - original.x0) / original.width
        fy1 = (region.y1 - original.y0) / original.height
        for idx in range(len(self.document)):
            target_rect = self.document[idx].rect
            local_region = (
                fitz.Rect(
                    target_rect.x0 + fx0 * target_rect.width,
                    target_rect.y0 + fy0 * target_rect.height,
                    target_rect.x0 + fx1 * target_rect.width,
                    target_rect.y0 + fy1 * target_rect.height,
                )
                & target_rect
            )
            if not local_region.is_empty:
                self.crops[idx] = tuple(local_region)
                self.free_crops.pop(idx, None)
        self.prepared_preview = None
        if self.preview_doc:
            self.preview_doc.close()
            self.preview_doc = None
        if self._preview_timer is not None:
            self.after_cancel(self._preview_timer)
            self._preview_timer = None
        self.source_preview_page = pno
        self.preview_status.configure(
            text="RECORTE APLICADO a todas las páginas y miniaturas."
        )
        self.update_thumbnails()
        self.preview()

    def clear_crop(self):
        if self.page.get() == "Selección de miniaturas" and self.selected_pages:
            for idx in self.selected_pages:
                self.crops.pop(idx, None)
                self.free_crops.pop(idx, None)
        else:
            self.crops.clear()
            self.free_crops.clear()
        self._crop_mode = False
        self.canvas.configure(cursor="")
        self.update_thumbnails()
        self.invalidate_preview()
