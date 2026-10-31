"""Document sessions and validated commands for the React desktop."""

import base64
import math
from pathlib import Path

import pymupdf as fitz

from grafiplot.constants import PAPERS, paper_rate
from grafiplot.core.layout import create_output
from grafiplot.core.pages import parse_excluded_pages, parse_page_order
from grafiplot.core.selection import selected_pdf

MODES = {
    "normal": "Normal",
    "poster": "Póster",
    "booklet": "Folleto",
    "nup": "Varias páginas por hoja",
}


class OutputMixin:
    def render(self, document_id, page=0, width=1000, preview=False):
        item = self._document(document_id)
        source = (
            self.previews.get(document_id, {}).get("path")
            if preview
            else item["source"]
        )
        if not source:
            raise ValueError("Prepare la vista de impresión primero.")
        with fitz.open(source) as pdf:
            page = int(page)
            if not 0 <= page < len(pdf):
                raise ValueError("Página fuera del documento.")
            rectangle = pdf[page].rect
            if not preview and page in item["crops"]:
                rectangle = fitz.Rect(item["crops"][page]) & rectangle
            scale = min(
                2.5,
                max(0.1, int(width) / max(rectangle.width, rectangle.height * 0.72)),
            )
            pixmap = pdf[page].get_pixmap(
                matrix=fitz.Matrix(scale, scale),
                clip=rectangle,
                alpha=False,
                colorspace=fitz.csRGB,
            )
            return {
                "image": "data:image/png;base64,"
                + base64.b64encode(pixmap.tobytes("png")).decode("ascii"),
                "width": pixmap.width,
                "height": pixmap.height,
                "pages": len(pdf),
            }

    def _parameters(self, settings):
        mode = settings.get("mode", "normal")
        if mode not in MODES:
            raise ValueError("Modo de impresión inválido.")
        paper_name = settings.get("paper", next(iter(PAPERS)))
        if paper_name not in PAPERS:
            raise ValueError("Formato de papel inválido.")
        paper = PAPERS[paper_name] or (
            float(settings.get("paperWidth", 210)),
            float(settings.get("paperHeight", 297)),
        )
        if not all(math.isfinite(v) and 30 <= v <= 2000 for v in paper):
            raise ValueError("Papel: entre 30 y 2000 mm.")
        margin = float(settings.get("margin", 5))
        overlap = float(settings.get("overlap", 5)) if mode == "poster" else 0
        if not 0 <= margin <= 100 or not 0 <= overlap <= 100:
            raise ValueError("Margen y solape: entre 0 y 100 mm.")
        cols, rows = (
            (int(settings.get("columns", 2)), int(settings.get("rows", 2)))
            if mode == "poster"
            else (1, 1)
        )
        if not 1 <= cols <= 30 or not 1 <= rows <= 30 or cols * rows > 300:
            raise ValueError("Póster: máximo 300 hojas, 30 por lado.")
        per_sheet = int(settings.get("perSheet", 2))
        if not 1 <= per_sheet <= 256:
            raise ValueError("Páginas por hoja: entre 1 y 256.")
        if mode == "nup":
            layout = settings.get("layout", "auto")
            if layout == "all":
                per_sheet = ("all",)
            elif layout == "grid":
                nc, nr = int(settings.get("nupColumns", 2)), int(
                    settings.get("nupRows", 2)
                )
                if not 1 <= nc <= 16 or not 1 <= nr <= 16:
                    raise ValueError("Cuadrícula: entre 1 y 16 por lado.")
                per_sheet = 1000 + nc * 100 + nr
            elif layout == "measure":
                cw, ch = float(settings.get("cellWidth", 50)), float(
                    settings.get("cellHeight", 70)
                )
                if not 5 <= cw <= 2000 or not 5 <= ch <= 2000:
                    raise ValueError("Medidas: entre 5 y 2000 mm.")
                per_sheet = ("measure", cw, ch)
        content = int(settings.get("content", 100))
        if not 25 <= content <= 200:
            raise ValueError("Contenido: entre 25 y 200 %.")
        return (
            MODES[mode],
            cols,
            rows,
            paper,
            settings.get("orientation") == "landscape",
            margin,
            overlap,
            -1,
            settings.get("scale", "Ajustar"),
            per_sheet,
            content,
            bool(settings.get("autorotate", True)),
            bool(settings.get("center", True)),
        )

    def prepare(self, document_id, settings):
        parameters = self._parameters(settings)
        copies = int(settings.get("copies", 1))
        if not 1 <= copies <= 9999:
            raise ValueError("Copias: entre 1 y 9999.")
        item = self._document(document_id)
        total = len(item["pdf"])
        omitted = parse_excluded_pages(settings.get("excluded", ""), total)
        if settings.get("order", "").strip():
            indexes = parse_page_order(settings["order"], total)
        elif settings.get("selectionOnly"):
            indexes = sorted(set(int(n) for n in settings.get("selected", [])))
        else:
            indexes = list(range(total))
        if any(n < 0 or n >= total for n in indexes):
            raise ValueError("Selección fuera del documento.")
        indexes = [n for n in indexes if n not in omitted]
        subset, output = self._path(), self._path()
        selected_pdf(item["pdf"], indexes, subset, item["crops"])
        try:
            count = create_output(subset, output, *parameters)
        finally:
            Path(subset).unlink(missing_ok=True)
        sheets = (
            math.ceil(
                count
                / (
                    2
                    if settings.get("duplex") or settings.get("mode") == "booklet"
                    else 1
                )
            )
            * copies
        )
        old = self.previews.get(document_id)
        if old:
            Path(old["path"]).unlink(missing_ok=True)
        self.previews[document_id] = {
            "path": output,
            "indexes": indexes,
            "settings": settings.copy(),
        }
        with fitz.open(output) as prepared:
            width = round(prepared[0].rect.width * 25.4 / 72, 1)
            height = round(prepared[0].rect.height * 25.4 / 72, 1)
        return {
            "pages": count,
            "sheets": sheets,
            "cost": round(sheets * paper_rate(settings.get("paper", "A4")), 2),
            "width": width,
            "height": height,
        }

    def _safe_target(self, path):
        target = Path(path).expanduser().resolve()
        if target.suffix.lower() != ".pdf":
            raise ValueError("El destino debe tener extensión .pdf.")
        if target.exists():
            raise ValueError(
                "El destino ya existe. Elija un nombre nuevo para conservar los archivos."
            )
        target.parent.mkdir(parents=True, exist_ok=True)
        return target

    def export(self, document_id, settings, path=None):
        result = self.prepare(document_id, settings)
        source = self.previews[document_id]["path"]
        if path:
            target = self._safe_target(path)
            with open(source, "rb") as inp, open(target, "xb") as out:
                import shutil

                shutil.copyfileobj(inp, out)
            return {**result, "path": str(target)}
        return {
            **result,
            "data": base64.b64encode(Path(source).read_bytes()).decode("ascii"),
        }
