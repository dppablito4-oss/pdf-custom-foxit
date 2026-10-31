"""Merge and pad documents into a new PDF."""

import datetime
import os
import shutil
import tempfile
import uuid
from pathlib import Path

import pymupdf as fitz

from grafiplot.core.conversion import make_pdf
from grafiplot.core.pages import parse_excluded_pages


def combined_destination(sources, output=None):
    """Always produce a new, unique PDF; never overwrite or remove source files."""
    source_paths = {
        os.path.normcase(os.path.realpath(os.path.abspath(str(p)))) for p in sources
    }
    if output:
        target = Path(output).expanduser().absolute()
        if os.path.normcase(os.path.realpath(str(target))) in source_paths:
            raise ValueError(
                "El destino coincide con un documento original. Elija otro nombre o carpeta."
            )
        if target.exists():
            raise FileExistsError(
                f"El archivo de destino ya existe: {target}. No se sobrescribirá."
            )
        target.parent.mkdir(parents=True, exist_ok=True)
        return target
    folder = Path.home() / "Documents" / "GRAFIPLOT PDF PRINT" / "Combinados"
    folder.mkdir(parents=True, exist_ok=True)
    while True:
        target = folder / (
            "GRAFIPLOT_COMBINADO_"
            + datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            + "_"
            + uuid.uuid4().hex[:6]
            + ".pdf"
        )
        if not target.exists():
            return target


def combine_documents(
    paths,
    output=None,
    work_dir=None,
    separator=False,
    exclusions=None,
    pad_odd=False,
    rotate_odd_landscape=False,
    duplex_mode=None,
    simplex_separator=False,
    pad_each_odd=False,
):
    """Merge without modifying sources. duplex: pad odd documents, add two blank separator pages.

    Orientation option rotates odd landscape pages 90 degrees left, even pages 90 right.
    """
    sources = [str(Path(p).expanduser().absolute()) for p in paths]
    if len(sources) < 2:
        raise ValueError("Seleccione al menos dos documentos.")
    for src in sources:
        if not os.path.isfile(src):
            raise FileNotFoundError(src)
    target = combined_destination(sources, output)
    combined = fitz.open()
    exclusions = exclusions or [""] * len(sources)
    if len(exclusions) != len(sources):
        raise ValueError("Cantidad incorrecta de exclusiones.")
    if duplex_mode is None:
        # Compatibility with old callers: the caller can still pass the legacy options.
        duplex_mode = bool(pad_odd or separator not in (False, "ninguno", None))
    try:
        with tempfile.TemporaryDirectory(
            prefix="grafiplot_merge_", dir=work_dir
        ) as folder:
            added_docs = 0
            for i, src in enumerate(sources):
                work = Path(folder) / f"archivo_{i:04d}"
                work.mkdir()
                converted = make_pdf(src, str(work))
                with fitz.open(converted) as part:
                    if part.needs_pass:
                        raise ValueError("PDF protegido: " + Path(src).name)
                    omitted = parse_excluded_pages(exclusions[i], part.page_count)
                    remaining = [n for n in range(part.page_count) if n not in omitted]
                    if not remaining:
                        continue
                    # Two fully blank sheets between documents, only in duplex mode.
                    # The preceding odd document is padded BEFORE the separator.
                    if (duplex_mode or simplex_separator) and added_docs:
                        for _ in range(2 if duplex_mode else 1):
                            reference = part[remaining[0]].rect
                            combined.new_page(
                                width=reference.width, height=reference.height
                            )
                    for position, n in enumerate(remaining, start=1):
                        before = combined.page_count
                        combined.insert_pdf(part, from_page=n, to_page=n)
                        page = combined[before]
                        if (
                            duplex_mode
                            and rotate_odd_landscape
                            and part[n].rect.width > part[n].rect.height
                        ):
                            # Odd: counter-clockwise 90 (270). Even: clockwise 90.
                            offset = 270 if position % 2 else 90
                            page.set_rotation((page.rotation + offset) % 360)
                    if (duplex_mode or pad_each_odd) and len(remaining) % 2:
                        last = part[remaining[-1]].rect
                        combined.new_page(width=last.width, height=last.height)
                    added_docs += 1
            if not combined.page_count:
                raise ValueError("No quedaron páginas para combinar.")
            temporary = str(target) + "." + uuid.uuid4().hex + ".part"
            try:
                combined.save(temporary, garbage=4, deflate=True)
                with open(temporary, "rb") as inp, open(target, "xb") as dst:
                    shutil.copyfileobj(inp, dst)
            finally:
                if os.path.exists(temporary):
                    os.unlink(temporary)
        return str(target), combined.page_count
    finally:
        combined.close()
