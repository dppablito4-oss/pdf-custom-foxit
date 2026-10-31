import { describe, expect, it } from "vitest";
import { selectionRect, intersects, mergeMarquee } from "./marquee";

describe("selección rectangular de páginas", () => {
  it("acepta arrastre en las cuatro direcciones", () => {
    expect(selectionRect({ x: 100, y: 200 }, { x: 10, y: 20 })).toEqual({
      left: 10,
      top: 20,
      right: 100,
      bottom: 200,
    });
    expect(selectionRect({ x: 10, y: 200 }, { x: 100, y: 20 })).toEqual({
      left: 10,
      top: 20,
      right: 100,
      bottom: 200,
    });
  });
  it("selecciona páginas intersectadas y excluye las que solo tocan el borde", () => {
    const a = { left: 0, top: 0, right: 100, bottom: 100 };
    expect(intersects(a, { left: 80, top: 80, right: 150, bottom: 150 })).toBe(
      true,
    );
    expect(intersects(a, { left: 100, top: 0, right: 150, bottom: 100 })).toBe(
      false,
    );
  });
  it("conserva la selección anterior en una selección aditiva sin duplicados", () => {
    expect(mergeMarquee([1, 4, 7], [0, 1, 2])).toEqual([0, 1, 2, 4, 7]);
  });
});
