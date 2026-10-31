import { useEffect, useRef, useState } from "react";
import {
  intersects,
  mergeMarquee,
  selectionRect,
  type Point,
  type Rect,
} from "../lib/marquee";

interface Drag {
  start: Point;
  client: Point;
  base: number[];
  pointerId: number;
  selected: number[];
  frame: number;
}
export function useMarqueeSelection(
  documentId: string,
  selected: number[],
  onChange: (selected: number[]) => void,
) {
  const container = useRef<HTMLDivElement>(null),
    drag = useRef<Drag | null>(null),
    callback = useRef(onChange),
    skipClick = useRef(false);
  const [rectangle, setRectangle] = useState<Rect | null>(null);
  callback.current = onChange;
  function finish() {
    const current = drag.current;
    if (!current) return;
    cancelAnimationFrame(current.frame);
    if (container.current?.hasPointerCapture(current.pointerId))
      container.current.releasePointerCapture(current.pointerId);
    drag.current = null;
    setRectangle(null);
    skipClick.current = true;
  }
  useEffect(() => {
    finish();
    skipClick.current = false;
    return () => {
      if (drag.current) cancelAnimationFrame(drag.current.frame);
      drag.current = null;
    };
  }, [documentId]);
  function tick() {
    const current = drag.current,
      element = container.current;
    if (!current || !element) return;
    const bounds = element.getBoundingClientRect();
    const edge = 32;
    if (current.client.y < bounds.top + edge)
      element.scrollTop -= Math.min(
        18,
        (bounds.top + edge - current.client.y) / 2,
      );
    if (current.client.y > bounds.bottom - edge)
      element.scrollTop += Math.min(
        18,
        (current.client.y - bounds.bottom + edge) / 2,
      );
    const end = {
      x:
        Math.max(0, Math.min(bounds.width, current.client.x - bounds.left)) +
        element.scrollLeft,
      y:
        Math.max(0, Math.min(bounds.height, current.client.y - bounds.top)) +
        element.scrollTop,
    };
    const area = selectionRect(current.start, end);
    setRectangle(area);
    const hits = Array.from(
      element.querySelectorAll<HTMLButtonElement>("[data-page]"),
    )
      .filter((button) => {
        const box = button.getBoundingClientRect();
        return intersects(area, {
          left: box.left - bounds.left + element.scrollLeft,
          top: box.top - bounds.top + element.scrollTop,
          right: box.right - bounds.left + element.scrollLeft,
          bottom: box.bottom - bounds.top + element.scrollTop,
        });
      })
      .map((button) => Number(button.dataset.page));
    const next = mergeMarquee(current.base, hits);
    if (next.join(",") !== current.selected.join(",")) {
      current.selected = next;
      callback.current(next);
    }
    current.frame = requestAnimationFrame(tick);
  }
  return {
    container,
    rectangle,
    handlers: {
      onPointerDown: (event: React.PointerEvent<HTMLDivElement>) => {
        if (
          event.button !== 0 ||
          (event.target as HTMLElement).closest("[data-page]")
        )
          return;
        event.preventDefault();
        const element = container.current!,
          bounds = element.getBoundingClientRect();
        const base =
          event.ctrlKey || event.metaKey || event.shiftKey ? [...selected] : [];
        drag.current = {
          start: {
            x: event.clientX - bounds.left + element.scrollLeft,
            y: event.clientY - bounds.top + element.scrollTop,
          },
          client: { x: event.clientX, y: event.clientY },
          base,
          pointerId: event.pointerId,
          selected: base,
          frame: 0,
        };
        element.setPointerCapture(event.pointerId);
        element.focus({ preventScroll: true });
        callback.current(base);
        tick();
      },
      onPointerMove: (event: React.PointerEvent<HTMLDivElement>) => {
        if (drag.current)
          drag.current.client = { x: event.clientX, y: event.clientY };
      },
      onPointerUp: finish,
      onPointerCancel: finish,
      onClickCapture: (event: React.MouseEvent) => {
        if (skipClick.current) {
          event.preventDefault();
          event.stopPropagation();
          skipClick.current = false;
        }
      },
    },
  };
}
