import { describe, expect, it } from "vitest";
import { togglePage, formatSize } from "./selection";
describe("selección de páginas", () => {
  it("reemplaza con clic simple", () =>
    expect(togglePage([0, 2], 4, "single", 0)).toEqual([4]));
  it("Ctrl+clic añade y quita", () => {
    expect(togglePage([0, 2], 1, "toggle", 0)).toEqual([0, 1, 2]);
    expect(togglePage([0, 2], 2, "toggle", 0)).toEqual([0]);
  });
  it("Shift+clic selecciona un rango sin duplicados", () => {
    expect(togglePage([0, 2], 5, "range", 2)).toEqual([0, 2, 3, 4, 5]);
    expect(togglePage([4], 1, "range", 4)).toEqual([1, 2, 3, 4]);
  });
});
describe("tamaño legible", () => {
  it("muestra KB y MB", () => {
    expect(formatSize(1024)).toBe("1 KB");
    expect(formatSize(1572864)).toBe("1.5 MB");
  });
});
