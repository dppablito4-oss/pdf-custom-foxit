import {
  FolderOpen,
  Save,
  Printer,
  Crop,
  MousePointer2,
  RotateCw,
  RotateCcw,
  Trash2,
  Undo2,
  Files,
  Combine,
  Settings2,
  CircleHelp,
} from "lucide-react";
import type { View } from "../types";
import { AppearanceControl } from "./AppearanceControl";

export type EditorTool = "select" | "crop";
interface Props {
  view: View;
  onView: (view: View) => void;
  busy: boolean;
  hasDocument: boolean;
  selected: number;
  tool: EditorTool;
  onTool: (tool: EditorTool) => void;
  onOpen: () => void;
  onSave: () => void;
  onPrint: () => void;
  onRotate: (degrees: number) => void;
  onDelete: () => void;
  onClearCrop: () => void;
  onHelp: () => void;
}

export function EditorHeader(p: Props) {
  return (
    <header className="editor-header">
      <div className="editor-titlebar">
        <h1>
          GRAFIPLOT <span>PDF</span>
        </h1>
        <button
          className="quick-open"
          title="Abrir documentos · Ctrl+O"
          aria-label="Abrir documentos"
          disabled={p.busy}
          onClick={p.onOpen}
        >
          <FolderOpen size={17} />
          Abrir
        </button>
        <div className="header-spacer" />
        <AppearanceControl />
        <button
          className="icon-button"
          title="Ayuda y atajos"
          aria-label="Guía rápida"
          onClick={p.onHelp}
        >
          <CircleHelp size={17} />
        </button>
      </div>
      <nav className="editor-tabs" aria-label="Herramientas del editor">
        {(
          [
            ["studio", "Inicio", Files],
            ["merge", "Combinar PDF", Combine],
            ["jobs", "Trabajos enviados", Printer],
            ["preferences", "Preferencias", Settings2],
          ] as const
        ).map(([view, label, Icon]) => (
          <button
            key={view}
            aria-current={p.view === view ? "page" : undefined}
            className={p.view === view ? "active" : ""}
            aria-label={view === "studio" ? "Documentos" : label}
            onClick={() => p.onView(view)}
          >
            <Icon size={15} />
            {label}
          </button>
        ))}
      </nav>
      {p.view === "studio" && (
        <div
          className="editor-ribbon"
          role="toolbar"
          aria-label="Herramientas de documento"
        >
          <div className="ribbon-group">
            <button
              disabled={!p.hasDocument || p.busy}
              onClick={p.onSave}
              title="Guardar PDF · Ctrl+S"
            >
              <Save size={20} />
              <span>Guardar PDF</span>
            </button>
            <button
              disabled={!p.hasDocument || p.busy}
              onClick={p.onPrint}
              title="Imprimir documento"
            >
              <Printer size={20} />
              <span>Imprimir</span>
            </button>
            <small>Archivo</small>
          </div>
          <div className="ribbon-group">
            <button
              disabled={!p.hasDocument || p.busy}
              className={p.tool === "select" ? "active" : ""}
              onClick={() => p.onTool("select")}
              aria-pressed={p.tool === "select"}
            >
              <MousePointer2 size={20} />
              <span>Seleccionar</span>
            </button>
            <button
              disabled={!p.hasDocument || p.busy}
              className={p.tool === "crop" ? "active" : ""}
              onClick={() => p.onTool(p.tool === "crop" ? "select" : "crop")}
              aria-label="Recortar con el mouse"
              aria-pressed={p.tool === "crop"}
            >
              <Crop size={20} />
              <span>Recortar</span>
            </button>
            <button
              disabled={!p.hasDocument || p.busy}
              onClick={p.onClearCrop}
              aria-label="Quitar recortes"
            >
              <Undo2 size={20} />
              <span>Quitar recorte</span>
            </button>
            <small>Herramientas</small>
          </div>
          <div className="ribbon-group">
            <button
              disabled={!p.selected || p.busy}
              onClick={() => p.onRotate(-90)}
              aria-label="Girar selección a la izquierda"
            >
              <RotateCcw size={20} />
              <span>Girar izquierda</span>
            </button>
            <button
              disabled={!p.selected || p.busy}
              onClick={() => p.onRotate(90)}
              aria-label="Girar selección"
            >
              <RotateCw size={20} />
              <span>Girar derecha</span>
            </button>
            <button
              disabled={!p.selected || p.busy}
              onClick={p.onDelete}
              aria-label="Quitar selección"
            >
              <Trash2 size={20} />
              <span>Eliminar</span>
            </button>
            <small>Páginas</small>
          </div>
          <div className="ribbon-note">
            {p.hasDocument
              ? p.selected
                ? `${p.selected} páginas seleccionadas`
                : "Selecciona páginas para editar"
              : "Sin documento"}
          </div>
        </div>
      )}
    </header>
  );
}
