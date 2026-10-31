"""Create independent working PDFs from ordered pages and optional crops."""

import io

import pymupdf as fitz
from PIL import Image, ImageDraw


def selected_pdf(source, indexes, output, crops=None, free_crops=None):
    """Keep text/vectors for rectangular crops; freehand masks require rasterization."""
    crops = crops or {}
    free_crops = free_crops or {}
    if not indexes:
        raise ValueError("No hay páginas para imprimir.")
    with fitz.open() as result:
        for number in indexes:
            original = source[number]
            if number in free_crops:
                polygon = free_crops[number]
                region = (
                    fitz.Rect(
                        min(x for x, y in polygon),
                        min(y for x, y in polygon),
                        max(x for x, y in polygon),
                        max(y for x, y in polygon),
                    )
                    & original.rect
                )
                if region.is_empty:
                    raise ValueError("Recorte libre vacío.")
                pixmap = original.get_pixmap(
                    matrix=fitz.Matrix(2, 2),
                    clip=region,
                    alpha=False,
                    colorspace=fitz.csRGB,
                )
                image = Image.frombytes(
                    "RGB", (pixmap.width, pixmap.height), pixmap.samples
                ).convert("RGBA")
                mask = Image.new("L", image.size, 0)
                ImageDraw.Draw(mask).polygon(
                    [((x - region.x0) * 2, (y - region.y0) * 2) for x, y in polygon],
                    fill=255,
                )
                image.putalpha(mask)
                stream = io.BytesIO()
                image.save(stream, format="PNG")
                page = result.new_page(width=region.width, height=region.height)
                page.insert_image(page.rect, stream=stream.getvalue())
            elif number in crops:
                region = fitz.Rect(crops[number]) & original.rect
                if region.is_empty:
                    raise ValueError("Recorte inválido.")
                page = result.new_page(width=region.width, height=region.height)
                if original.get_contents():
                    page.show_pdf_page(
                        page.rect, source, number, clip=region, keep_proportion=False
                    )
            else:
                result.insert_pdf(source, from_page=number, to_page=number)
        result.save(output, garbage=4, deflate=True)
    return str(output)
