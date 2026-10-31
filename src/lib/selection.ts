export function togglePage(
  selected: number[],
  page: number,
  modifier: "single" | "toggle" | "range",
  anchor: number,
): number[] {
  if (modifier === "single") return [page];
  if (modifier === "range") {
    const low = Math.min(anchor, page),
      high = Math.max(anchor, page);
    return [
      ...new Set([
        ...selected,
        ...Array.from({ length: high - low + 1 }, (_, n) => low + n),
      ]),
    ].sort((a, b) => a - b);
  }
  return selected.includes(page)
    ? selected.filter((n) => n !== page)
    : [...selected, page].sort((a, b) => a - b);
}
export function formatSize(bytes: number) {
  return bytes >= 1048576
    ? `${(bytes / 1048576).toFixed(1)} MB`
    : `${Math.ceil(bytes / 1024)} KB`;
}
