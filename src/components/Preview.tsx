import { useEffect, useRef, useState } from "react";
import {
  ChevronLeft,
  ChevronRight,
  ZoomIn,
  ZoomOut,
  Maximize,
  LoaderCircle,
  Eye,
  Layers,
  FileText,
} from "lucide-react";
import { engine } from "../lib/engine";
import type { DocumentTab, PreviewInfo } from "../types";
import type { EditorTool } from "./EditorHeader";

export function EmptyState() {
  return (
    <div className="editor-empty">
      <FileText size={38} strokeWidth={1} />
      <span>Sin documento</span>
      <small>Ctrl+O para abrir · Arrastra archivos a la ventana</small>
    </div>
  );
}

interface Props {
  tab: DocumentTab;
  preview: PreviewInfo | null;
  previewVersion: number;
  preparing: boolean;
  onPage: (page: number) => void;
  onCrop: (crop: number[]) => void;
  onPrepare: () => void;
  tool: EditorTool;
  onToolChange: (tool: EditorTool) => void;
}
export function Preview({
  tab,
  preview,
  previewVersion,
  preparing,
  onPage,
  onCrop,
  onPrepare,
  tool,
  onToolChange,
}: Props) {
  const [output, setOutput] = useState(false),
    [outputPage, setOutputPage] = useState(0),
    [zoom, setZoom] = useState(1),
    [image, setImage] = useState(""),
    [loading, setLoading] = useState(false),
    [error, setError] = useState(""),
    [selection, setSelection] = useState<number[] | null>(null);
  const cropping = tool === "crop";
  const setCropping = (value: boolean) =>
    onToolChange(value ? "crop" : "select");
  useEffect(() => {
    if (cropping) {
      setOutput(false);
      setSelection(null);
    }
  }, [cropping]);
  const imageRef = useRef<HTMLImageElement>(null),
    start = useRef<number[] | null>(null);
  const count = output && preview ? preview.pages : tab.pages;
  const page = output ? Math.min(outputPage, count - 1) : tab.page;
  useEffect(() => {
    setOutputPage(0);
  }, [previewVersion]);
  useEffect(() => {
    if (!preview) setOutput(false);
  }, [preview]);
  useEffect(() => {
    setZoom(1);
    setOutput(false);
    setCropping(false);
  }, [tab.id]);
  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError("");
    engine<{ image: string }>("render", {
      document_id: tab.id,
      page,
      width: 1100,
      preview: output && !!preview,
    })
      .then((result) => {
        if (!cancelled) setImage(result.image);
      })
      .catch((error) => {
        if (!cancelled) setError(String(error));
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [tab.id, tab.revision, page, output, previewVersion, preview]);
  function coordinate(e: React.PointerEvent) {
    const rect = imageRef.current!.getBoundingClientRect();
    return [
      Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width)),
      Math.max(0, Math.min(1, (e.clientY - rect.top) / rect.height)),
    ];
  }
  return (
    <section className="preview-panel">
      <div className="preview-toolbar">
        <div className="segmented preview-switch">
          <button
            className={!output ? "selected" : ""}
            onClick={() => {
              setOutput(false);
              setCropping(false);
            }}
          >
            <Eye size={14} />
            Original
          </button>
          <button
            disabled={!preview}
            className={output ? "selected" : ""}
            onClick={() => {
              setOutput(true);
              setCropping(false);
            }}
          >
            <Layers size={14} />
            Impresión
          </button>
        </div>
        <div className="preview-tools">
          <button
            className="icon-button"
            title="Alejar"
            aria-label="Alejar"
            onClick={() => setZoom(Math.max(0.3, zoom - 0.15))}
          >
            <ZoomOut size={17} />
          </button>
          <span className="zoom-value">{Math.round(zoom * 100)}%</span>
          <button
            className="icon-button"
            title="Acercar"
            aria-label="Acercar"
            onClick={() => setZoom(Math.min(3, zoom + 0.15))}
          >
            <ZoomIn size={17} />
          </button>
          <button
            className="icon-button"
            title="Ajustar a ventana"
            aria-label="Ajustar a ventana"
            onClick={() => setZoom(1)}
          >
            <Maximize size={16} />
          </button>
        </div>
      </div>
      <div
        className={`preview-canvas ${cropping ? "cropping" : ""}`}
        onWheel={(e) => {
          if (e.ctrlKey) {
            e.preventDefault();
            setZoom((v) =>
              Math.max(0.3, Math.min(3, v + (e.deltaY < 0 ? 0.1 : -0.1))),
            );
          }
        }}
      >
        {cropping && (
          <div className="crop-instruction">
            Arrastra sobre la página. Se aplica a la selección o a todas las
            páginas.
          </div>
        )}
        {error ? (
          <div className="preview-error">
            <p>{error}</p>
            <button className="button" onClick={onPrepare}>
              Volver a preparar
            </button>
          </div>
        ) : (
          <div
            className="paper-wrap"
            style={{
              width: `${zoom * minPageWidth(tab, output, preview)}px`,
              maxWidth: zoom === 1 ? "85%" : undefined,
            }}
          >
            {image && (
              <img
                ref={imageRef}
                className="document-preview"
                src={image}
                alt={`Vista ${output ? "de impresión" : "original"}, página ${page + 1}`}
                draggable={false}
                onPointerDown={(e) => {
                  if (!cropping) return;
                  e.currentTarget.setPointerCapture(e.pointerId);
                  start.current = coordinate(e);
                  setSelection(null);
                }}
                onPointerMove={(e) => {
                  if (!start.current || !cropping) return;
                  const end = coordinate(e);
                  setSelection([
                    Math.min(start.current[0], end[0]),
                    Math.min(start.current[1], end[1]),
                    Math.max(start.current[0], end[0]),
                    Math.max(start.current[1], end[1]),
                  ]);
                }}
                onPointerUp={() => {
                  start.current = null;
                  if (
                    selection &&
                    selection[2] - selection[0] > 0.02 &&
                    selection[3] - selection[1] > 0.02
                  ) {
                    onCrop(selection);
                    setCropping(false);
                    setSelection(null);
                  }
                }}
              />
            )}
            {selection && (
              <span
                className="crop-rectangle"
                style={{
                  left: `${selection[0] * 100}%`,
                  top: `${selection[1] * 100}%`,
                  width: `${(selection[2] - selection[0]) * 100}%`,
                  height: `${(selection[3] - selection[1]) * 100}%`,
                }}
              />
            )}
            {!image && (
              <div className="paper-loading">
                <LoaderCircle className="spin" size={25} />
              </div>
            )}
          </div>
        )}
        {(loading || preparing) && (
          <span className="render-status">
            <LoaderCircle size={13} className="spin" />
            {preparing ? "Preparando impresión" : "Renderizando página"}
          </span>
        )}
      </div>
      <div className="preview-footer">
        <span>
          <i className={preview ? "ready-dot" : "waiting-dot"} />
          {output ? "Vista de impresión" : "Documento original"}
          {preview && !output && (
            <button className="text-button" onClick={() => setOutput(true)}>
              Ver resultado →
            </button>
          )}
        </span>
        <div className="page-navigation">
          <button
            className="icon-button"
            aria-label="Página anterior"
            disabled={page === 0}
            onClick={() =>
              output ? setOutputPage(page - 1) : onPage(page - 1)
            }
          >
            <ChevronLeft size={17} />
          </button>
          <span>
            {page + 1}
            <small> / {count}</small>
          </span>
          <button
            className="icon-button"
            aria-label="Página siguiente"
            disabled={page >= count - 1}
            onClick={() =>
              output ? setOutputPage(page + 1) : onPage(page + 1)
            }
          >
            <ChevronRight size={17} />
          </button>
        </div>
        <span className="dimension-label">
          {tab.width} × {tab.height} mm
        </span>
      </div>
    </section>
  );
}
function minPageWidth(
  tab: DocumentTab,
  output: boolean,
  preview: PreviewInfo | null,
) {
  return (
    output && preview ? preview.width > preview.height : tab.width > tab.height
  )
    ? 760
    : 505;
}
