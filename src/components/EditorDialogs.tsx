import { X } from "lucide-react";
export function EditorDialogs({
  help,
  confirm,
  count,
  busy,
  onCloseHelp,
  onCloseConfirm,
  onDelete,
}: {
  help: boolean;
  confirm: boolean;
  count: number;
  busy: boolean;
  onCloseHelp: () => void;
  onCloseConfirm: () => void;
  onDelete: () => void;
}) {
  return (
    <>
      {confirm && (
        <div className="modal-backdrop">
          <div
            className="modal"
            role="dialog"
            aria-modal="true"
            aria-labelledby="delete-title"
          >
            <h2 id="delete-title">Eliminar {count} páginas</h2>
            <p>
              Se eliminarán de la copia de trabajo. El archivo original se
              conserva.
            </p>
            <div className="modal-actions">
              <button className="button" onClick={onCloseConfirm}>
                Cancelar
              </button>
              <button
                className="button primary"
                disabled={busy}
                onClick={onDelete}
              >
                Eliminar páginas
              </button>
            </div>
          </div>
        </div>
      )}
      {help && (
        <div className="modal-backdrop">
          <div
            className="modal help-modal"
            role="dialog"
            aria-modal="true"
            aria-labelledby="help-title"
          >
            <button
              className="icon-button modal-close"
              aria-label="Cerrar guía"
              onClick={onCloseHelp}
            >
              <X size={18} />
            </button>
            <h2 id="help-title">Herramientas y atajos</h2>
            <dl className="shortcut-list">
              <dt>Ctrl+O</dt>
              <dd>Abrir documentos</dd>
              <dt>Ctrl+S</dt>
              <dd>Guardar PDF preparado</dd>
              <dt>Ctrl+Tab</dt>
              <dd>Cambiar documento</dd>
              <dt>Ctrl+clic</dt>
              <dd>Añadir o quitar una página de la selección</dd>
              <dt>Shift+clic</dt>
              <dd>Seleccionar un rango</dd>
              <dt>Arrastrar</dt>
              <dd>Dibujar una selección desde un espacio entre miniaturas</dd>
              <dt>Ctrl+A</dt>
              <dd>Seleccionar todas las miniaturas</dd>
              <dt>Supr</dt>
              <dd>Eliminar páginas de la copia</dd>
              <dt>Escape</dt>
              <dd>Cancelar la herramienta o limpiar selección</dd>
            </dl>
            <p>
              Arrastra el borde del panel de páginas para cambiar su ancho.
              «Preferencias del driver» abre las opciones de papel, calidad y
              tinta disponibles en tu impresora.
            </p>
          </div>
        </div>
      )}
    </>
  );
}
