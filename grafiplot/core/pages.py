"""Page selection and exclusion parsing."""


def parse_excluded_pages(spec, total):
    """1-based comma/ranges; excludes pages only from generated copy."""
    bad = set()
    for part in spec.replace(";", ",").split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            bits = part.split("-")
            if len(bits) != 2 or not all(x.strip().isdigit() for x in bits):
                raise ValueError("Rango inválido: " + part)
            a, b = map(int, bits)
            if a > b:
                raise ValueError("Rango descendente: " + part)
            if not 1 <= a <= b <= total:
                raise ValueError(f"Páginas permitidas: 1 a {total}")
            bad.update(range(a, b + 1))
        elif part.isdigit():
            bad.add(int(part))
        else:
            raise ValueError("Página inválida: " + part)
    if any(n < 1 or n > total for n in bad):
        raise ValueError(f"Páginas permitidas: 1 a {total}")
    return {n - 1 for n in bad}


def parse_page_order(spec, total, limit=10000):
    """Return zero-based indexes, retaining duplicates; validate before expanding ranges."""
    indexes = []
    for item in spec.replace(";", ",").split(","):
        token = item.strip()
        if not token:
            raise ValueError("Hay una posición vacía en la lista de páginas.")
        parts = token.split("-")
        if len(parts) not in (1, 2) or not all(p.strip().isdigit() for p in parts):
            raise ValueError("Página o rango inválido: " + token)
        first = int(parts[0])
        last = int(parts[-1])
        if first > last:
            raise ValueError("El rango debe ser ascendente: " + token)
        if not 1 <= first <= last <= total:
            raise ValueError(f"Indique páginas entre 1 y {total}.")
        if len(indexes) + last - first + 1 > limit:
            raise ValueError("Máximo de 10 000 páginas por trabajo.")
        indexes.extend(range(first - 1, last))
    return indexes
