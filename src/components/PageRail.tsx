import { useEffect, useRef, useState } from "react";
import { Check, CheckCheck, Minus } from "lucide-react";
import { engine } from "../lib/engine";
import type { DocumentTab } from "../types";
import { useMarqueeSelection } from "../hooks/useMarqueeSelection";
export type PageSelectionModifier = "single" | "toggle" | "range";
function Thumbnail({
  tab,
  page,
  selected,
  sent,
  onClick,
}: {
  tab: DocumentTab;
  page: number;
  selected: boolean;
  sent: boolean;
  onClick: (e: React.MouseEvent) => void;
}) {
  const ref = useRef<HTMLButtonElement>(null);
  const [visible, setVisible] = useState(false),
    [image, setImage] = useState("");
  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting) {
          setVisible(true);
          observer.disconnect();
        }
      },
      { rootMargin: "150px" },
    );
    if (ref.current) observer.observe(ref.current);
    return () => observer.disconnect();
  }, []);
  useEffect(() => {
    if (!visible) return;
    let cancelled = false;
    setImage("");
    engine<{ image: string }>("render", {
      document_id: tab.id,
      page,
      width: 170,
    })
      .then((result) => {
        if (!cancelled) setImage(result.image);
      })
      .catch(() => {});
    return () => {
      cancelled = true;
    };
  }, [visible, tab.id, tab.revision, page]);
  return (
    <button
      ref={ref}
      data-page={page}
      className={`thumbnail ${selected ? "selected" : ""} ${sent ? "sent" : ""} ${tab.page === page ? "current" : ""}`}
      onClick={onClick}
      aria-label={`Página ${page + 1}`}
      aria-pressed={selected}
    >
      <div className="thumbnail-paper">
        {image ? (
          <img src={image} alt="" draggable={false} />
        ) : (
          <span className="thumbnail-placeholder" />
        )}
        {selected && (
          <span className="thumb-check">
            <Check size={11} />
          </span>
        )}
        {sent && <span className="sent-dot" title="Enviada a impresión" />}
      </div>
      <span className="page-number">{String(page + 1).padStart(2, "0")}</span>
    </button>
  );
}
export function PageRail({
  tab,
  onSelect,
  onAll,
  onClear,
  onSelectionChange,
  busy,
}: {
  tab: DocumentTab;
  onSelect: (page: number, modifier: PageSelectionModifier) => void;
  onAll: () => void;
  onClear: () => void;
  onSelectionChange: (pages: number[]) => void;
  busy: boolean;
}) {
  const [width, setWidth] = useState(() => {
    try {
      return Math.max(
        140,
        Math.min(
          520,
          Number(localStorage.getItem("grafiplot.pages.width")) || 220,
        ),
      );
    } catch {
      return 220;
    }
  });
  const [size, setSize] = useState(100),
    [resizing, setResizing] = useState(false);
  const panel = useRef<HTMLElement>(null),
    resizeStart = useRef<{ x: number; width: number } | null>(null);
  const marquee = useMarqueeSelection(tab.id, tab.selected, onSelectionChange);
  const maxWidth = () =>
    Math.max(
      140,
      Math.min(560, (panel.current?.parentElement?.clientWidth || 900) - 327),
    );
  useEffect(() => {
    try {
      localStorage.setItem("grafiplot.pages.width", String(width));
    } catch {
      /* Session layout still works. */
    }
  }, [width]);
  useEffect(() => {
    const parent = panel.current?.parentElement;
    if (!parent) return;
    const observer = new ResizeObserver(() =>
      setWidth((value) => Math.min(value, maxWidth())),
    );
    observer.observe(parent);
    return () => observer.disconnect();
  }, []);
  function navigate(event: React.KeyboardEvent<HTMLDivElement>) {
    if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "a") {
      event.preventDefault();
      onAll();
      return;
    }
    if (event.key === "Escape") {
      event.preventDefault();
      onClear();
      return;
    }
    const buttons = Array.from(
      marquee.container.current!.querySelectorAll<HTMLButtonElement>(
        "[data-page]",
      ),
    );
    const focused = (event.target as HTMLElement).closest<HTMLButtonElement>(
      "[data-page]",
    );
    const index = focused ? Number(focused.dataset.page) : tab.page;
    const columns = Math.max(
      1,
      buttons.filter((button) => button.offsetTop === buttons[0]?.offsetTop)
        .length,
    );
    let next = index;
    if (event.key === "ArrowRight") next++;
    else if (event.key === "ArrowLeft") next--;
    else if (event.key === "ArrowDown") next += columns;
    else if (event.key === "ArrowUp") next -= columns;
    else if (event.key === "Home") next = 0;
    else if (event.key === "End") next = tab.pages - 1;
    else if (event.key === " " && focused) {
      event.preventDefault();
      onSelect(index, "toggle");
      return;
    } else return;
    event.preventDefault();
    next = Math.max(0, Math.min(tab.pages - 1, next));
    buttons[next]?.focus({ preventScroll: true });
    buttons[next]?.scrollIntoView({ block: "nearest" });
    if (!event.ctrlKey && !event.metaKey)
      onSelect(next, event.shiftKey ? "range" : "single");
  }
  return (
    <>
      <section
        ref={panel}
        className={`page-rail ${resizing ? "resizing" : ""}`}
        style={{ width }}
        aria-label="Panel de páginas"
      >
        <div className="rail-heading">
          <h3>
            Páginas <span>{tab.pages}</span>
          </h3>
          <div>
            <button
              className="icon-button"
              title="Seleccionar todas · Ctrl+A"
              aria-label="Seleccionar todas"
              disabled={busy}
              onClick={onAll}
            >
              <CheckCheck size={17} />
            </button>
            <button
              className="icon-button"
              title="Limpiar selección"
              aria-label="Limpiar selección"
              disabled={busy}
              onClick={onClear}
            >
              <Minus size={17} />
            </button>
          </div>
        </div>
        <label className="thumbnail-size">
          <span>Tamaño</span>
          <input
            type="range"
            aria-label="Tamaño de miniaturas"
            min={75}
            max={170}
            value={size}
            onChange={(event) => setSize(Number(event.target.value))}
          />
        </label>
        <div
          ref={marquee.container}
          className="thumbnails"
          style={
            {
              "--thumbnail-size": `${Math.min(size, width - 40)}px`,
            } as React.CSSProperties
          }
          tabIndex={0}
          role="group"
          aria-label="Miniaturas de páginas"
          onKeyDown={navigate}
          {...(busy ? {} : marquee.handlers)}
        >
          {Array.from({ length: tab.pages }, (_, page) => (
            <Thumbnail
              key={`${tab.id}-${page}`}
              tab={tab}
              page={page}
              selected={tab.selected.includes(page)}
              sent={tab.sent.includes(page)}
              onClick={(event) =>
                onSelect(
                  page,
                  event.shiftKey
                    ? "range"
                    : event.ctrlKey || event.metaKey
                      ? "toggle"
                      : "single",
                )
              }
            />
          ))}
          {marquee.rectangle && (
            <span
              className="marquee-selection"
              style={{
                left: marquee.rectangle.left,
                top: marquee.rectangle.top,
                width: marquee.rectangle.right - marquee.rectangle.left,
                height: marquee.rectangle.bottom - marquee.rectangle.top,
              }}
            />
          )}
        </div>
        <div className="rail-bottom">
          <span>{tab.selected.length} seleccionadas</span>
          <small>Arrastrar: seleccionar · Ctrl: añadir</small>
        </div>
      </section>
      <div
        className={`page-splitter ${resizing ? "active" : ""}`}
        role="separator"
        aria-label="Ancho del panel de páginas"
        title="Arrastra para cambiar el ancho · Doble clic para restablecer"
        aria-orientation="vertical"
        aria-valuemin={140}
        aria-valuemax={maxWidth()}
        aria-valuenow={Math.round(width)}
        tabIndex={0}
        onPointerDown={(event) => {
          if (event.button !== 0) return;
          event.preventDefault();
          resizeStart.current = { x: event.clientX, width };
          setResizing(true);
          event.currentTarget.setPointerCapture(event.pointerId);
        }}
        onPointerMove={(event) => {
          if (resizeStart.current)
            setWidth(
              Math.max(
                140,
                Math.min(
                  maxWidth(),
                  resizeStart.current.width +
                    event.clientX -
                    resizeStart.current.x,
                ),
              ),
            );
        }}
        onPointerUp={(event) => {
          resizeStart.current = null;
          setResizing(false);
          if (event.currentTarget.hasPointerCapture(event.pointerId))
            event.currentTarget.releasePointerCapture(event.pointerId);
        }}
        onPointerCancel={() => {
          resizeStart.current = null;
          setResizing(false);
        }}
        onDoubleClick={() => setWidth(220)}
        onKeyDown={(event) => {
          if (["ArrowLeft", "ArrowRight", "Home", "End"].includes(event.key)) {
            event.preventDefault();
            setWidth((value) =>
              event.key === "Home"
                ? 140
                : event.key === "End"
                  ? maxWidth()
                  : Math.max(
                      140,
                      Math.min(
                        maxWidth(),
                        value + (event.key === "ArrowRight" ? 20 : -20),
                      ),
                    ),
            );
          }
        }}
      >
        <span />
      </div>
    </>
  );
}
