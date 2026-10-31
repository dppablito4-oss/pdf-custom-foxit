"""SumatraPDF requests; see https://www.sumatrapdfreader.org/docs/Command-line-arguments."""

import os
import shutil
from pathlib import Path

DEFAULT_PRINTER = "Impresora predeterminada"


def find_sumatra():
    candidates = [
        shutil.which("SumatraPDF.exe"),
        r"C:\Program Files\SumatraPDF\SumatraPDF.exe",
        r"C:\Program Files (x86)\SumatraPDF\SumatraPDF.exe",
        str(Path.home() / "AppData/Local/SumatraPDF/SumatraPDF.exe"),
    ]
    return next((path for path in candidates if path and os.path.isfile(path)), None)


def build_print_command(
    executable,
    path,
    printer=DEFAULT_PRINTER,
    paper="A4",
    copies=1,
    duplex=False,
    booklet=False,
    scale="noscale",
):
    """Keep all settings in a single flag so copies cannot replace paper/duplex."""
    copies = int(copies)
    if not 1 <= copies <= 9999:
        raise ValueError("Número de copias entre 1 y 9999.")
    if scale not in ("noscale", "fit", "shrink"):
        raise ValueError("Escala de impresión inválida.")
    target = (
        ["-print-to-default"] if printer == DEFAULT_PRINTER else ["-print-to", printer]
    )
    settings = [scale, f"{copies}x"]
    paper = {"Carta": "Letter"}.get(paper, paper)
    if paper in ("A4", "A3", "A2", "A1", "A0", "Letter", "Legal"):
        settings.append("paper=" + paper)
    settings.append("duplexshort" if booklet else ("duplex" if duplex else "simplex"))
    return [
        str(executable),
        *target,
        "-print-settings",
        ",".join(settings),
        "-silent",
        str(path),
    ]
