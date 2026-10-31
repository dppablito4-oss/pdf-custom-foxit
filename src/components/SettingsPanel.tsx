import {
  ChevronDown,
  Info,
  Printer,
  Settings2,
  SlidersHorizontal,
  RefreshCw,
  ArrowRight,
} from "lucide-react";
import type {
  DocumentTab,
  EngineInfo,
  Mode,
  PrintSettings,
  PreviewInfo,
} from "../types";

interface Props {
  tab: DocumentTab;
  info: EngineInfo;
  update: (patch: Partial<PrintSettings>) => void;
  preview: PreviewInfo | null;
  printer: string;
  setPrinter: (value: string) => void;
  printing: boolean;
  disabled: boolean;
  onPrint: () => void;
  onExport: () => void;
  onDriver: (properties: boolean) => void;
  onRefresh: () => void;
}
export function SettingsPanel({
  tab,
  info,
  update,
  preview,
  printer,
  setPrinter,
  printing,
  disabled,
  onPrint,
  onExport,
  onDriver,
  onRefresh,
}: Props) {
  const s = tab.settings;
  const number = (
    key: keyof PrintSettings,
    label: string,
    min: number,
    max: number,
    step = 1,
  ) => (
    <label className="field">
      <span>{label}</span>
      <input
        type="number"
        min={min}
        max={max}
        step={step}
        value={s[key] as number}
        onChange={(e) => update({ [key]: Number(e.target.value) })}
      />
    </label>
  );
  return (
    <aside className="settings-panel">
      <div className="printer-configuration">
        <div className="printer-heading">
          <Printer size={19} />
          <h2>Impresora</h2>
          <button
            className="icon-button"
            title="Actualizar impresoras"
            aria-label="Actualizar impresoras"
            disabled={disabled}
            onClick={onRefresh}
          >
            <RefreshCw size={16} />
          </button>
        </div>
        <label className="printer-select">
          <select
            aria-label="Impresora"
            value={printer}
            onChange={(event) => setPrinter(event.target.value)}
          >
            {info.printers.map((p) => (
              <option key={p} value={p}>
                {p === "Impresora predeterminada" && info.defaultPrinter
                  ? `Predeterminada: ${info.defaultPrinter}`
                  : p}
              </option>
            ))}
          </select>
        </label>
        <div className="driver-actions">
          <button
            disabled={disabled}
            onClick={() => onDriver(false)}
            title="Abrir el controlador para modificar papel, calidad y tinta"
          >
            <SlidersHorizontal size={16} />
            Preferencias del driver
          </button>
          <button disabled={disabled} onClick={() => onDriver(true)}>
            <Settings2 size={16} />
            Propiedades
          </button>
        </div>
      </div>
      <div className="settings-scroll">
        <section className="setting-section">
          <h3>Modo de impresión</h3>
          <label className="field mode-field">
            <select
              aria-label="Modo de impresión"
              value={s.mode}
              onChange={(event) =>
                update({
                  mode: event.target.value as Mode,
                  duplex: event.target.value === "booklet" ? true : s.duplex,
                })
              }
            >
              <option value="normal">Normal</option>
              <option value="poster">Póster</option>
              <option value="booklet">Folleto</option>
              <option value="nup">Varias páginas por hoja</option>
            </select>
          </label>
          {s.mode === "booklet" && (
            <div className="inline-note">
              <Info size={15} />
              <span>Cuadernillo a doble cara con giro por borde corto.</span>
            </div>
          )}
          {s.mode === "poster" && (
            <>
              <div className="field-row">
                {number("columns", "Columnas", 1, 30)}
                {number("rows", "Filas", 1, 30)}
              </div>
              {number("overlap", "Solape entre hojas · mm", 0, 100)}
            </>
          )}
          {s.mode === "nup" && (
            <>
              <label className="field">
                <span>Distribución</span>
                <select
                  value={s.layout}
                  onChange={(e) => update({ layout: e.target.value })}
                >
                  <option value="auto">Automática</option>
                  <option value="grid">Columnas y filas</option>
                  <option value="all">Todas en una hoja</option>
                  <option value="measure">A medida en mm</option>
                </select>
              </label>
              {s.layout === "auto" &&
                number("perSheet", "Páginas por hoja", 1, 256)}
              {s.layout === "grid" && (
                <div className="field-row">
                  {number("nupColumns", "Columnas", 1, 16)}
                  {number("nupRows", "Filas", 1, 16)}
                </div>
              )}
              {s.layout === "measure" && (
                <>
                  <div className="field-row">
                    {number("cellWidth", "Ancho · mm", 5, 2000)}
                    {number("cellHeight", "Alto · mm", 5, 2000)}
                  </div>
                  <p className="field-hint">
                    Separación de 5 mm entre páginas.
                  </p>
                  <label className="check">
                    <input
                      type="checkbox"
                      checked={s.center}
                      onChange={(e) => update({ center: e.target.checked })}
                    />
                    Centrar conjunto en la hoja
                  </label>
                </>
              )}
            </>
          )}
        </section>
        <section className="setting-section">
          <h3>Papel y tamaño</h3>
          <label className="field">
            <span>Formato del papel</span>
            <select
              value={s.paper}
              onChange={(e) => update({ paper: e.target.value })}
            >
              {Object.keys(info.papers).map((paper) => (
                <option key={paper}>{paper}</option>
              ))}
            </select>
          </label>
          {s.paper === "Personalizado" && (
            <div className="field-row">
              {number("paperWidth", "Ancho · mm", 30, 2000)}
              {number("paperHeight", "Alto · mm", 30, 2000)}
            </div>
          )}
          <div className="segmented orientation">
            <button
              className={s.orientation === "portrait" ? "selected" : ""}
              onClick={() => update({ orientation: "portrait" })}
            >
              <span className="paper-icon" />
              Vertical
            </button>
            <button
              className={s.orientation === "landscape" ? "selected" : ""}
              onClick={() => update({ orientation: "landscape" })}
            >
              <span className="paper-icon horizontal" />
              Horizontal
            </button>
          </div>
          <div className="field-row">
            {number("margin", "Margen · mm", 0, 100, 0.5)}
            {number("content", "Contenido · %", 25, 200, 5)}
          </div>
          <label className="check">
            <input
              type="checkbox"
              checked={s.autorotate}
              onChange={(e) => update({ autorotate: e.target.checked })}
            />
            Autorrotar para aprovechar papel
          </label>
        </section>
        <section className="setting-section">
          <h3>Páginas y acabado</h3>
          <label className="field">
            <span>Páginas a imprimir</span>
            <select
              value={s.selectionOnly ? "selected" : "all"}
              onChange={(e) =>
                update({ selectionOnly: e.target.value === "selected" })
              }
            >
              <option value="all">Todas las páginas</option>
              <option value="selected">
                Selección de miniaturas ({tab.selected.length})
              </option>
            </select>
          </label>
          <div className="field-row">
            {number("copies", "Copias", 1, 9999)}
            <label className="field">
              <span>Impresión</span>
              <select
                disabled={s.mode === "booklet"}
                value={s.duplex ? "duplex" : "simplex"}
                onChange={(e) =>
                  update({ duplex: e.target.value === "duplex" })
                }
              >
                <option value="simplex">Una cara</option>
                <option value="duplex">Doble cara</option>
              </select>
            </label>
          </div>
          <details>
            <summary>
              Opciones avanzadas
              <ChevronDown size={15} />
            </summary>
            <label className="field">
              <span>Escala</span>
              <select
                value={s.scale}
                onChange={(e) => update({ scale: e.target.value })}
              >
                {[
                  "Ajustar",
                  "Tamaño real (100%)",
                  "Estirar para llenar (deformar)",
                ].map((value) => (
                  <option key={value}>{value}</option>
                ))}
              </select>
            </label>
            <label className="field">
              <span>Orden personalizado</span>
              <input
                placeholder="Ej.: 1, 1, 3, 5-8"
                value={s.order}
                onChange={(e) => update({ order: e.target.value })}
              />
            </label>
            <label className="field">
              <span>Excluir páginas</span>
              <input
                placeholder="Ej.: 2, 4, 7-10"
                value={s.excluded}
                onChange={(e) => update({ excluded: e.target.value })}
              />
            </label>
          </details>
        </section>
      </div>
      <div className="print-card">
        <div className="estimate">
          <span>
            Estimado de impresión
            <small>
              {preview
                ? `${preview.sheets} hojas físicas · ${s.copies} copia${s.copies === 1 ? "" : "s"}`
                : "Prepara la vista de impresión"}
            </small>
          </span>
          <strong>{preview ? `S/ ${preview.cost.toFixed(2)}` : "—"}</strong>
        </div>
        <button
          className="button primary print-button"
          disabled={disabled}
          onClick={onPrint}
        >
          <Printer size={17} />
          {printing ? "Enviando…" : "Imprimir documento"}
          <ArrowRight size={17} />
        </button>
        <button className="export-link" disabled={disabled} onClick={onExport}>
          O guardar como PDF
        </button>
      </div>
    </aside>
  );
}
