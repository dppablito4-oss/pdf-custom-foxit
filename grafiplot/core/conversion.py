"""Convert supported formats without changing the source."""

import os
import shutil
import subprocess
from pathlib import Path

import pymupdf as fitz
from PIL import Image, ImageOps

from grafiplot.constants import IMAGES, OFFICE
from grafiplot.core.external import system_dll_search, system_environment


def make_pdf(path, cache_dir):
    ext = Path(path).suffix.lower()
    if ext == ".pdf":
        return path
    out = os.path.join(cache_dir, "entrada.pdf")
    if ext in IMAGES:
        # Convert each frame of a multipage TIFF/GIF to a separate PDF page. Original stays untouched.
        doc = fitz.open()
        try:
            with Image.open(path) as source_image:
                for index in range(getattr(source_image, "n_frames", 1)):
                    source_image.seek(index)
                    frame = ImageOps.exif_transpose(source_image).convert("RGB")
                    dpi_value = source_image.info.get("dpi", (150, 150))
                    if isinstance(dpi_value, (tuple, list)):
                        dpi_value = dpi_value[0]
                    try:
                        dpi = max(72, min(600, float(dpi_value or 150)))
                    except (ValueError, TypeError):
                        dpi = 150
                    w, h = frame.size
                    page = doc.new_page(width=w * 72 / dpi, height=h * 72 / dpi)
                    import io

                    buffer = io.BytesIO()
                    frame.save(buffer, format="PNG")
                    page.insert_image(page.rect, stream=buffer.getvalue())
            doc.save(out, deflate=True)
        finally:
            doc.close()
        return out
    if ext == ".svg":
        try:
            import cairosvg
        except ImportError:
            raise RuntimeError("Para SVG instale CairoSVG: pip install cairosvg")
        cairosvg.svg2pdf(url=path, write_to=out)
        return out
    if ext in OFFICE:
        exe = shutil.which("soffice") or shutil.which("libreoffice")
        if not exe:
            candidates = [
                r"C:\Program Files\LibreOffice\program\soffice.exe",
                r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
            ]
            exe = next((p for p in candidates if os.path.exists(p)), None)
        if not exe:
            raise RuntimeError(
                "Se necesita LibreOffice para abrir Word/Excel/PowerPoint. Ejecute INSTALAR_TODO_WINDOWS.bat para instalar los complementos."
            )
        with system_dll_search():
            result = subprocess.run(
                [
                    exe,
                    "-env:UserInstallation=file:///"
                    + cache_dir.replace("\\", "/").replace(" ", "%20")
                    + "/lo_profile",
                    "--headless",
                    "--convert-to",
                    "pdf",
                    "--outdir",
                    cache_dir,
                    path,
                ],
                capture_output=True,
                text=True,
                timeout=120,
                env=system_environment(),
            )
        converted = os.path.join(cache_dir, Path(path).stem + ".pdf")
        if result.returncode or not os.path.exists(converted):
            raise RuntimeError(
                "No se pudo convertir el documento: " + result.stderr[:400]
            )
        return converted
    raise ValueError("Formato no compatible: " + ext)
