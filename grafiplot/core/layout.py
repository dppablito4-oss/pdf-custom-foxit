"""Vector-preserving normal, poster, booklet and N-up output."""

import math
from contextlib import ExitStack

import pymupdf as fitz


def points(mm):
    return mm * 72 / 25.4


def make_booklet(
    src, out, paper_mm, landscape, margin_mm, page_number=-1, stretch=False
):
    """Booklet imposition, 2 original pages per side, 4 pages per physical sheet.
    Output order is front then back, suitable for short-edge duplex printing.
    """
    with ExitStack() as documents:
        original = documents.enter_context(fitz.open(src))
        ids = list(range(len(original))) if page_number == -1 else [page_number]
        # Four logical pages per folded physical sheet, pad with blanks.
        ids += [None] * ((-len(ids)) % 4)
        pw, ph = map(points, paper_mm)
        # A horizontal sheet is necessary for a conventional side-by-side booklet.
        if not landscape and ph > pw:
            pw, ph = ph, pw
        elif landscape and pw < ph:
            pw, ph = ph, pw
        margin = points(margin_mm)
        if 2 * margin >= min(ph, pw / 2):
            raise ValueError("Margen demasiado grande para folleto.")
        output = documents.enter_context(fitz.open())
        left = 0
        right = len(ids) - 1
        while left < right:
            # front: last+first; back: second+second-last
            for pair in ((ids[right], ids[left]), (ids[left + 1], ids[right - 1])):
                pg = output.new_page(width=pw, height=ph)
                for col, pid in enumerate(pair):
                    if pid is None:
                        continue
                    box = fitz.Rect(
                        col * pw / 2 + margin,
                        margin,
                        (col + 1) * pw / 2 - margin,
                        ph - margin,
                    )
                    place_pdf_page(pg, box, original, pid, keep_proportion=not stretch)
            left += 2
            right -= 2
        output.save(out, garbage=4, deflate=True)
        return len(output)


def make_nup(
    src,
    out,
    paper_mm,
    landscape,
    margin_mm,
    page_number=-1,
    per_sheet=2,
    stretch=False,
    grid=None,
    cell_mm=None,
    gap_mm=None,
    center=True,
):
    """Vector-preserving N-up. Grid can be explicitly set as (columns, rows)."""
    with ExitStack() as documents:
        if not 1 <= per_sheet <= 10000:
            raise ValueError("Cantidad de páginas por hoja fuera de rango.")
        original = documents.enter_context(fitz.open(src))
        if original.needs_pass:
            raise ValueError("PDF protegido.")
        ids = list(range(len(original))) if page_number == -1 else [page_number]
        pw, ph = map(points, paper_mm)
        if landscape:
            pw, ph = ph, pw
        m = points(margin_mm)
        if m * 2 >= min(pw, ph):
            raise ValueError("Margen demasiado grande.")
        printable_w, printable_h = pw - 2 * m, ph - 2 * m
        if cell_mm is not None:
            cw, ch = map(points, cell_mm)
            gap = points(5 if gap_mm is None else gap_mm)
            if cw <= 0 or ch <= 0 or gap < 0:
                raise ValueError("Ancho, alto o separación inválidos.")
            cols = max(0, int((printable_w + gap + 1e-6) // (cw + gap)))
            rows = max(0, int((printable_h + gap + 1e-6) // (ch + gap)))
            if cols < 1 or rows < 1:
                raise ValueError(
                    "Las dimensiones elegidas no caben en el papel. Reduzca ancho/alto o margen."
                )
            if cols * rows > 10000:
                raise ValueError("Demasiadas páginas por hoja.")
            per_sheet = cols * rows
        elif grid is not None:
            cols, rows = map(int, grid)
            if cols < 1 or rows < 1 or cols * rows != per_sheet:
                raise ValueError("Cuadrícula inválida.")
        else:
            # Evaluate the actual page aspect ratios rather than assuming all pages are A4.
            candidates = []
            for cols0 in range(1, min(per_sheet, 256) + 1):
                rows0 = math.ceil(per_sheet / cols0)
                area = 0.0
                for pid in ids[: min(per_sheet, len(ids))]:
                    sp = original[pid].rect
                    boxw = printable_w / cols0
                    boxh = printable_h / rows0
                    ratio = min(boxw / sp.width, boxh / sp.height)
                    area += ratio * ratio * sp.width * sp.height
                candidates.append((area, -(cols0 * rows0 - per_sheet), cols0, rows0))
            _, _, cols, rows = max(candidates)
        # Small cell gap preserves the maximum printable surface; the physical margin is user controlled.
        gap = (
            points(5 if gap_mm is None else gap_mm)
            if cell_mm is not None
            else min(points(0.35), max(0, m / 8))
        )
        # Centrar la cuadrícula completa dentro del área imprimible.
        if cell_mm is not None:
            grid_w = cols * cw + (cols - 1) * gap
            grid_h = rows * ch + (rows - 1) * gap
            grid_x = m + (printable_w - grid_w) / 2 if center else m
            grid_y = m + (printable_h - grid_h) / 2 if center else m
        result = documents.enter_context(fitz.open())
        for start in range(0, len(ids), per_sheet):
            page = result.new_page(width=pw, height=ph)
            for slot, pid in enumerate(ids[start : start + per_sheet]):
                r, c = divmod(slot, cols)
                if cell_mm is not None:
                    cw, ch = map(points, cell_mm)
                    x0 = grid_x + c * (cw + gap)
                    y0 = grid_y + r * (ch + gap)
                    x1 = x0 + cw
                    y1 = y0 + ch
                else:
                    x0 = m + c * printable_w / cols + gap
                    y0 = m + r * printable_h / rows + gap
                    x1 = m + (c + 1) * printable_w / cols - gap
                    y1 = m + (r + 1) * printable_h / rows - gap
                if x1 > x0 and y1 > y0:
                    place_pdf_page(
                        page,
                        fitz.Rect(x0, y0, x1, y1),
                        original,
                        pid,
                        keep_proportion=not stretch,
                    )
        result.save(out, garbage=4, deflate=True)
        return len(result)


def create_output(
    source,
    output,
    mode,
    cols,
    rows,
    paper_mm,
    landscape,
    margin_mm,
    overlap_mm,
    page_number=0,
    scale="Ajustar",
    per_sheet=2,
    content_pct=100,
    autorotate=False,
    nup_center=True,
):
    with ExitStack() as documents:
        if mode == "Varias páginas por hoja":
            grid = None
            cell_mm = None
            gap_mm = None
            if isinstance(per_sheet, tuple):
                if per_sheet[0] == "all":
                    with fitz.open(source) as doc:
                        per_sheet = max(1, len(doc) if page_number == -1 else 1)
                elif per_sheet[0] == "measure":
                    cell_mm = (per_sheet[1], per_sheet[2])
                    gap_mm = 5
                    per_sheet = 1
            elif per_sheet >= 1000:
                encoded = per_sheet - 1000
                grid = (encoded // 100, encoded % 100)
                per_sheet = grid[0] * grid[1]
            return make_nup(
                source,
                output,
                paper_mm,
                landscape,
                margin_mm,
                page_number,
                per_sheet,
                scale == "Estirar para llenar (deformar)",
                grid=grid,
                cell_mm=cell_mm,
                gap_mm=gap_mm,
                center=nup_center,
            )
        if mode == "Folleto":
            return make_booklet(
                source,
                output,
                paper_mm,
                landscape,
                margin_mm,
                page_number,
                scale == "Estirar para llenar (deformar)",
            )
        src = documents.enter_context(fitz.open(source))
        if src.needs_pass:
            raise ValueError("PDF protegido: abra un PDF sin contraseña.")
        if page_number >= len(src):
            raise ValueError("Página inexistente.")
        wmm, hmm = paper_mm
        if landscape:
            wmm, hmm = hmm, wmm
        pw, ph = points(wmm), points(hmm)
        margin = points(margin_mm)
        overlap = points(overlap_mm)
        if margin * 2 >= min(pw, ph):
            raise ValueError("El margen excede el tamaño del papel.")
        page_ids = range(len(src)) if page_number == -1 else [page_number]
        out = documents.enter_context(fitz.open())
        for pid in page_ids:
            sp = src[pid]
            r = sp.rect
            if autorotate and mode == "Normal":
                # Rotate only when landscape-vs-portrait mismatch improves the fit.
                rotate_page = (r.width > r.height) != (pw > ph)
            else:
                rotate_page = False
            if mode == "Normal":
                dst = out.new_page(width=pw, height=ph)
                avail = fitz.Rect(margin, margin, pw - margin, ph - margin)
                if scale == "Tamaño real (100%)":
                    tw = min(r.width, avail.width)
                    th = min(r.height, avail.height)
                    clip = fitz.Rect(0, 0, tw, th)
                    dest = fitz.Rect(avail.x0, avail.y0, avail.x0 + tw, avail.y0 + th)
                    place_pdf_page(
                        dst, dest, src, pid, clip=clip, keep_proportion=False
                    )
                else:
                    factor = max(0.1, min(2.5, float(content_pct) / 100.0))
                    slot = fitz.Rect(
                        avail.x0 + (avail.width * (1 - factor) / 2),
                        avail.y0 + (avail.height * (1 - factor) / 2),
                        avail.x1 - (avail.width * (1 - factor) / 2),
                        avail.y1 - (avail.height * (1 - factor) / 2),
                    )
                    slot = slot & dst.rect
                    if slot.is_empty:
                        slot = avail
                    place_pdf_page(
                        dst,
                        slot,
                        src,
                        pid,
                        keep_proportion=scale != "Estirar para llenar (deformar)",
                        rotate=90 if rotate_page else 0,
                    )
            else:
                # Output is physical paper tiles; overlap is repeated across adjacent sheets.
                usable_w = pw - 2 * margin
                usable_h = ph - 2 * margin
                stride_w = usable_w - overlap
                stride_h = usable_h - overlap
                if stride_w <= 0 or stride_h <= 0:
                    raise ValueError("La superposición es demasiado grande.")
                total_w = usable_w + (cols - 1) * stride_w
                total_h = usable_h + (rows - 1) * stride_h
                factor = min(total_w / r.width, total_h / r.height) * max(
                    0.1, min(2.5, float(content_pct) / 100)
                )
                stretch = scale == "Estirar para llenar (deformar)"
                # Optional distortion only on request.
                draw_w = total_w if stretch else r.width * factor
                draw_h = total_h if stretch else r.height * factor
                offset_x = (total_w - draw_w) / 2
                offset_y = (total_h - draw_h) / 2
                for row in range(rows):
                    for col in range(cols):
                        dst = out.new_page(width=pw, height=ph)
                        x0 = col * stride_w
                        y0 = row * stride_h
                        # intersect tile's global printable box with scaled source placement
                        ix0 = max(x0, offset_x)
                        iy0 = max(y0, offset_y)
                        ix1 = min(x0 + usable_w, offset_x + draw_w)
                        iy1 = min(y0 + usable_h, offset_y + draw_h)
                        if ix1 <= ix0 or iy1 <= iy0:
                            continue
                        clip = fitz.Rect(
                            (ix0 - offset_x) * r.width / draw_w,
                            (iy0 - offset_y) * r.height / draw_h,
                            (ix1 - offset_x) * r.width / draw_w,
                            (iy1 - offset_y) * r.height / draw_h,
                        )
                        target = fitz.Rect(
                            margin + ix0 - x0,
                            margin + iy0 - y0,
                            margin + ix1 - x0,
                            margin + iy1 - y0,
                        )
                        place_pdf_page(
                            dst, target, src, pid, clip=clip, keep_proportion=False
                        )
                        # discreet trim guide at printable corners
                        sh = dst.new_shape()
                        tick = points(2.5)
                        for x in [margin, pw - margin]:
                            for y in [margin, ph - margin]:
                                dd = 1 if x == margin else -1
                                ee = 1 if y == margin else -1
                                sh.draw_line((x, y), (x + dd * tick, y))
                                sh.draw_line((x, y), (x, y + ee * tick))
                        sh.finish(color=(0.6, 0.6, 0.6), width=0.35)
                        sh.commit()
        out.save(output, garbage=4, deflate=True)
        n = len(out)
        return n


def place_pdf_page(target, rectangle, source, page_number, **options):
    """Preserve intentional blank separator pages without asking MuPDF to place empty content."""
    if source[page_number].get_contents():
        target.show_pdf_page(rectangle, source, page_number, **options)
