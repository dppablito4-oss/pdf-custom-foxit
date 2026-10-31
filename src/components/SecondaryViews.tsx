import { useState } from "react";
import {
  ArrowDown,
  ArrowUp,
  Combine,
  FileText,
  Plus,
  Trash2,
  RefreshCw,
  Printer,
  Save,
  Check,
  X,
} from "lucide-react";
import type { DocumentTab, EngineInfo, Job } from "../types";
import { DEFAULT_PRINTER } from "../types";

export interface MergeOptions {
  document_ids: string[];
  exclusions: string[];
  duplex: boolean;
  separator: boolean;
  pad_odd: boolean;
  rotate: boolean;
}
export function MergeView({
  tabs,
  onOpen,
  onMerge,
  busy,
}: {
  tabs: DocumentTab[];
  onOpen: () => void;
  onMerge: (options: MergeOptions) => void;
  busy: boolean;
}) {
  const [items, setItems] = useState(
      tabs.map((tab) => ({ id: tab.id, excluded: "" })),
    ),
    [duplex, setDuplex] = useState(false),
    [separator, setSeparator] = useState(false),
    [pad, setPad] = useState(false),
    [rotate, setRotate] = useState(false);
  const available = tabs.filter(
    (tab) => !items.some((item) => item.id === tab.id),
  );
  const move = (index: number, step: number) =>
    setItems((value) => {
      const next = [...value];
      [next[index], next[index + step]] = [next[index + step], next[index]];
      return next;
    });
  return (
    <div className="secondary-view">
      <div className="view-intro">
        <h2>Combinar documentos</h2>
        <p>Ordena los documentos y elige las páginas para combinar.</p>
      </div>
      <div className="merge-layout">
        <div className="surface merge-list">
          <div className="section-header">
            <h3>
              Orden de los documentos{" "}
              <span className="badge">{items.length}</span>
            </h3>
            <button className="button small" onClick={onOpen} disabled={busy}>
              <Plus size={15} />
              Abrir archivos
            </button>
          </div>
          {items.map((item, index) => {
            const tab = tabs.find((tab) => tab.id === item.id);
            if (!tab) return null;
            return (
              <div className="merge-item" key={item.id}>
                <span className="merge-index">
                  {String(index + 1).padStart(2, "0")}
                </span>
                <span className="file-type-icon">
                  <FileText size={23} />
                </span>
                <div className="merge-item-info">
                  <strong>{tab.name}</strong>
                  <small>{tab.pages} páginas</small>
                  <input
                    aria-label={`Excluir páginas de ${tab.name}`}
                    placeholder="Excluir páginas: ej. 2, 5-8"
                    value={item.excluded}
                    onChange={(e) =>
                      setItems(
                        items.map((i) =>
                          i.id === item.id
                            ? { ...i, excluded: e.target.value }
                            : i,
                        ),
                      )
                    }
                  />
                </div>
                <div className="merge-item-actions">
                  <button
                    className="icon-button"
                    title="Subir"
                    disabled={index === 0 || busy}
                    onClick={() => move(index, -1)}
                  >
                    <ArrowUp size={16} />
                  </button>
                  <button
                    className="icon-button"
                    title="Bajar"
                    disabled={index === items.length - 1 || busy}
                    onClick={() => move(index, 1)}
                  >
                    <ArrowDown size={16} />
                  </button>
                  <button
                    className="icon-button danger"
                    title="Quitar de la combinación"
                    disabled={busy}
                    onClick={() =>
                      setItems(items.filter((i) => i.id !== item.id))
                    }
                  >
                    <Trash2 size={16} />
                  </button>
                </div>
              </div>
            );
          })}
          {!items.length && (
            <div className="inline-empty">
              <Combine size={35} />
              <p>Abre documentos para comenzar tu combinación.</p>
            </div>
          )}
          {available.length > 0 && (
            <div className="available-files">
              <span>Añadir documentos abiertos</span>
              {available.map((tab) => (
                <button
                  key={tab.id}
                  className="button small"
                  onClick={() =>
                    setItems([...items, { id: tab.id, excluded: "" }])
                  }
                >
                  <Plus size={14} />
                  {tab.name}
                </button>
              ))}
            </div>
          )}
        </div>
        <div className="surface merge-options">
          <h3>El resultado, a tu medida</h3>
          <label className="option-card">
            <input
              type="radio"
              checked={!duplex}
              onChange={() => setDuplex(false)}
              name="merge-mode"
            />
            <div>
              <strong>Una cara</strong>
              <p>Combina las páginas sin añadir separadores.</p>
            </div>
          </label>
          <label className="option-card">
            <input
              type="radio"
              checked={duplex}
              onChange={() => {
                setDuplex(true);
                setSeparator(false);
              }}
              name="merge-mode"
            />
            <div>
              <strong>Doble cara</strong>
              <p>
                Completa documentos impares y añade dos páginas blancas entre
                archivos.
              </p>
            </div>
          </label>
          <label className="check">
            <input
              type="checkbox"
              checked={pad}
              onChange={(e) => setPad(e.target.checked)}
            />
            Completar cada documento impar
          </label>
          <label className="check">
            <input
              type="checkbox"
              checked={separator}
              disabled={duplex}
              onChange={(e) => setSeparator(e.target.checked)}
            />
            Una página separadora
          </label>
          <label className="check">
            <input
              type="checkbox"
              checked={rotate}
              disabled={!duplex}
              onChange={(e) => setRotate(e.target.checked)}
            />
            Alternar giro en horizontales
          </label>
          <button
            className="button primary"
            disabled={items.length < 2 || busy}
            onClick={() =>
              onMerge({
                document_ids: items.map((i) => i.id),
                exclusions: items.map((i) => i.excluded),
                duplex,
                separator,
                pad_odd: pad,
                rotate,
              })
            }
          >
            <Combine size={17} />
            Combinar y abrir PDF
          </button>
          <p className="field-hint">
            El resultado se abre en otra pestaña. Tus originales se conservan.
          </p>
        </div>
      </div>
    </div>
  );
}

export function JobsView({
  jobs,
  onReport,
  busy,
}: {
  jobs: Job[];
  onReport: (client: string, print?: boolean) => void;
  busy: boolean;
}) {
  const [client, setClient] = useState("");
  const filtered = jobs.filter((job) => !client || job.client === client);
  return (
    <div className="secondary-view">
      <div className="view-intro">
        <h2>Trabajos enviados</h2>
        <p>
          Consulta las solicitudes enviadas y prepara un reporte por cliente.
        </p>
      </div>
      <div className="job-summary">
        <div className="surface">
          <span>Trabajos enviados</span>
          <strong>{filtered.length.toString().padStart(2, "0")}</strong>
        </div>
        <div className="surface">
          <span>Hojas estimadas</span>
          <strong>{filtered.reduce((n, j) => n + j.sheets, 0)}</strong>
        </div>
        <div className="surface">
          <span>Importe referencial</span>
          <strong>
            S/ {filtered.reduce((n, j) => n + j.cost, 0).toFixed(2)}
          </strong>
        </div>
      </div>
      <div className="surface">
        <div className="section-header">
          <h3>Historial de esta sesión</h3>
          <div className="inline-actions">
            <select
              aria-label="Filtrar por cliente"
              value={client}
              onChange={(e) => setClient(e.target.value)}
            >
              <option value="">Todos los clientes</option>
              {[...new Set(jobs.map((j) => j.client).filter(Boolean))].map(
                (c) => (
                  <option key={c}>{c}</option>
                ),
              )}
            </select>
            <button
              className="button small"
              disabled={busy}
              onClick={() => onReport(client)}
            >
              <FileText size={15} />
              Exportar reporte
            </button>
            <button
              className="button small"
              disabled={busy}
              onClick={() => onReport(client, true)}
            >
              <Printer size={15} />
              Imprimir A4
            </button>
          </div>
        </div>
        {!filtered.length ? (
          <div className="inline-empty">
            <Printer size={36} />
            <h3>Sin trabajos enviados</h3>
            <p>Las solicitudes de impresión aparecerán aquí.</p>
          </div>
        ) : (
          <div className="table-scroll">
            <table>
              <thead>
                <tr>
                  <th>Documento</th>
                  <th>Cliente</th>
                  <th>Impresora</th>
                  <th>Hojas</th>
                  <th>Importe</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((job, index) => (
                  <tr key={index}>
                    <td>
                      <strong>{job.name}</strong>
                      <small>
                        {job.date.replace("T", " · ")} · {job.copies} copias
                      </small>
                    </td>
                    <td>{job.client || "Sin asignar"}</td>
                    <td>{job.printer}</td>
                    <td>{job.sheets}</td>
                    <td>S/ {job.cost.toFixed(2)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
      <p className="view-footnote">
        El estado «enviado» registra la solicitud. No confirma la salida física
        de la impresora.
      </p>
    </div>
  );
}

export function PreferencesView({
  info,
  onRefresh,
  onSave,
  onPrinter,
  busy,
}: {
  info: EngineInfo;
  onRefresh: () => void;
  onSave: (routes: Record<string, string>) => void;
  onPrinter: (printer: string, properties: boolean) => void;
  busy: boolean;
}) {
  const [routes, setRoutes] = useState(info.routes),
    [printer, setPrinter] = useState(DEFAULT_PRINTER);
  return (
    <div className="secondary-view preferences">
      <div className="view-intro">
        <h2>Preferencias de impresión</h2>
        <p>
          Conecta tus impresoras y asigna un destino a cada formato de papel.
        </p>
      </div>
      <div className="surface">
        <div className="section-header">
          <h3>Impresoras del equipo</h3>
          <button className="button small" disabled={busy} onClick={onRefresh}>
            <RefreshCw size={14} />
            Actualizar
          </button>
        </div>
        <div className="preferences-content">
          <label className="field">
            <span>Impresora para configurar</span>
            <select
              value={printer}
              onChange={(e) => setPrinter(e.target.value)}
            >
              {info.printers.map((p) => (
                <option key={p}>{p}</option>
              ))}
            </select>
          </label>
          <div className="inline-actions">
            <button
              className="button small"
              disabled={busy}
              onClick={() => onPrinter(printer, false)}
            >
              Preferencias de impresión
            </button>
            <button
              className="button small"
              disabled={busy}
              onClick={() => onPrinter(printer, true)}
            >
              Propiedades
            </button>
          </div>
          <div className="connection-status">
            <span className={info.sumatra ? "status-good" : "status-missing"}>
              {info.sumatra ? <Check size={16} /> : <X size={16} />}
            </span>
            <div>
              <strong>
                {info.sumatra
                  ? "Impresión directa disponible"
                  : "SumatraPDF no detectado"}
              </strong>
              <p>
                {info.sumatra
                  ? "El motor de impresión está listo."
                  : "Puedes exportar PDF. Instala SumatraPDF para enviar a una impresora."}
              </p>
            </div>
          </div>
        </div>
      </div>
      <div className="surface">
        <div className="section-header">
          <h3>Asignación automática por papel</h3>
          <button
            className="button small"
            disabled={busy}
            onClick={() => onSave(routes)}
          >
            <Save size={14} />
            Guardar asignaciones
          </button>
        </div>
        <div className="preferences-content route-grid">
          {Object.keys(info.papers).map((paper) => (
            <label className="field" key={paper}>
              <span>{paper}</span>
              <select
                value={routes[paper] || DEFAULT_PRINTER}
                onChange={(e) =>
                  setRoutes({ ...routes, [paper]: e.target.value })
                }
              >
                {info.printers.map((p) => (
                  <option key={p}>{p}</option>
                ))}
              </select>
            </label>
          ))}
          <label className="field">
            <span>Impresora de reportes A4</span>
            <select
              value={routes._report_printer || DEFAULT_PRINTER}
              onChange={(e) =>
                setRoutes({ ...routes, _report_printer: e.target.value })
              }
            >
              {info.printers.map((p) => (
                <option key={p}>{p}</option>
              ))}
            </select>
          </label>
        </div>
      </div>
    </div>
  );
}
