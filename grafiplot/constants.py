"""Paper formats, supported extensions and default rates."""

PAPERS = {
    "A4 (210 × 297 mm)": (210, 297),
    "A3 (297 × 420 mm)": (297, 420),
    "A2 (420 × 594 mm)": (420, 594),
    "A1 (594 × 841 mm)": (594, 841),
    "A0 (841 × 1189 mm)": (841, 1189),
    "Carta (216 × 279 mm)": (215.9, 279.4),
    "Oficio (216 × 330 mm)": (215.9, 330.2),
    "Legal (216 × 356 mm)": (215.9, 355.6),
    "Tabloide (279 × 432 mm)": (279.4, 431.8),
    "Personalizado": None,
}

IMAGES = {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff", ".webp", ".gif"}

OFFICE = {
    ".doc",
    ".docx",
    ".xls",
    ".xlsx",
    ".ppt",
    ".pptx",
    ".odt",
    ".ods",
    ".odp",
    ".rtf",
    ".txt",
}

SAMPLE = "PDF e imágenes (incluido TIFF multipágina), Word, Excel y PowerPoint vía LibreOffice. Los originales no se alteran."

ARCHIVES = {".zip", ".rar"}

SUPPORTED_MERGE = {".pdf", ".svg"} | IMAGES | OFFICE

MAX_ARCHIVE_FILES = 500

MAX_ARCHIVE_BYTES = 1_000_000_000

PRICES = {"A4": 0.10, "A3": 0.50, "A2": 1.50, "A1": 2.00, "A0": 4.00}


def paper_rate(paper):
    # Carta, oficio y personalizado: precio provisional como A4; editable en siguiente versión.
    return PRICES.get(paper.split(" ", 1)[0], 0.10)
