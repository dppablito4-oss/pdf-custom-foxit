import { useEffect, useState } from "react";
import { X, FileText, AlertCircle } from "lucide-react";
import { EditorHeader, type EditorTool } from "./components/EditorHeader";
import { EditorDialogs } from "./components/EditorDialogs";
import { SettingsPanel } from "./components/SettingsPanel";
import { PageRail } from "./components/PageRail";
import { Preview, EmptyState } from "./components/Preview";
import {
  MergeView,
  JobsView,
  PreferencesView,
} from "./components/SecondaryViews";
import { desktop, engine } from "./lib/engine";
import { togglePage, formatSize } from "./lib/selection";
import { useStudio } from "./hooks/useStudio";

export default function App() {
  const studio = useStudio();
  const {
    view,
    setView,
    tabs,
    active,
    setActive,
    info,
    printer,
    setPrinter,
    busy,
    printing,
    preparing,
    preview,
    setPreview,
    previewVersion,
    jobs,
    toast,
    setToast,
    help,
    setHelp,
    confirm,
    setConfirm,
    dragging,
    setDragging,
    tab,
    anchor,
    notify,
    openDocuments,
    refresh,
    updateTab,
    updateSettings,
    prepare,
    closeTab,
    exportDocument,
    edit,
    printDocument,
    merge,
    report,
    saveRoutes,
    browserDrop,
  } = studio;
  const [tool, setTool] = useState<EditorTool>("select");
  useEffect(() => {
    setTool("select");
  }, [active]);
  useEffect(() => {
    const cancel = (event: KeyboardEvent) => {
      if (event.key === "Escape") setTool("select");
    };
    window.addEventListener("keydown", cancel);
    return () => window.removeEventListener("keydown", cancel);
  }, []);
  const driver = (properties: boolean) => {
    void engine("printer_dialog", { printer, properties }).catch((error) =>
      notify(String(error), true),
    );
  };
  return (
    <div
      className="app-shell editor-shell"
      onDragOver={(event) => {
        event.preventDefault();
        if (!desktop && event.dataTransfer.types.includes("Files"))
          setDragging(true);
      }}
      onDrop={browserDrop}
      onDragLeave={(event) => {
        if (!event.currentTarget.contains(event.relatedTarget as Node))
          setDragging(false);
      }}
    >
      <main className="main-shell">
        <EditorHeader
          view={view}
          onView={setView}
          busy={busy || preparing}
          hasDocument={!!tab}
          selected={tab?.selected.length || 0}
          tool={tool}
          onTool={setTool}
          onOpen={() => void openDocuments()}
          onSave={() => void exportDocument()}
          onPrint={() => void printDocument()}
          onRotate={(degrees) => void edit("rotate", undefined, degrees)}
          onDelete={() => setConfirm(true)}
          onClearCrop={() => void edit("clear_crop")}
          onHelp={() => setHelp(true)}
        />
        {view === "studio" ? (
          <>
            <div className="document-bar">
              <div className="document-tabs">
                {tabs.map((item) => (
                  <div
                    className={`document-tab ${active === item.id ? "active" : ""}`}
                    key={item.id}
                  >
                    <button
                      title={item.name}
                      onClick={() => {
                        setActive(item.id);
                        setPreview(null);
                      }}
                    >
                      <FileText size={14} />
                      <span>{item.name}</span>
                    </button>
                    <button
                      className="close-tab"
                      aria-label={`Cerrar ${item.name}`}
                      disabled={busy}
                      onClick={() => void closeTab(item.id)}
                    >
                      <X size={13} />
                    </button>
                  </div>
                ))}
              </div>
            </div>
            {tab ? (
              <>
                <div className="document-context">
                  <span className="document-metadata">
                    {tab.pages} páginas · {formatSize(tab.size)}
                  </span>
                  <label className="client-field">
                    Cliente / pedido
                    <input
                      aria-label="Cliente / pedido"
                      placeholder="Sin asignar"
                      value={tab.client}
                      onChange={(event) =>
                        updateTab({ client: event.target.value })
                      }
                    />
                  </label>
                </div>
                <div className="studio-workspace">
                  <div className="document-workspace">
                    <PageRail
                      tab={tab}
                      busy={busy}
                      onSelect={(page, modifier) => {
                        const selected = togglePage(
                          tab.selected,
                          page,
                          modifier,
                          anchor.current,
                        );
                        if (modifier !== "range") anchor.current = page;
                        updateTab({
                          page,
                          selected,
                          settings: {
                            ...tab.settings,
                            selectionOnly: selected.length > 0,
                          },
                        });
                      }}
                      onAll={() =>
                        updateTab({
                          selected: Array.from(
                            { length: tab.pages },
                            (_, i) => i,
                          ),
                          settings: { ...tab.settings, selectionOnly: false },
                        })
                      }
                      onClear={() =>
                        updateTab({
                          selected: [],
                          settings: { ...tab.settings, selectionOnly: false },
                        })
                      }
                      onSelectionChange={(selected) =>
                        updateTab({
                          selected,
                          settings: {
                            ...tab.settings,
                            selectionOnly: selected.length > 0,
                          },
                        })
                      }
                    />
                    <Preview
                      tab={tab}
                      preview={preview}
                      previewVersion={previewVersion}
                      preparing={preparing}
                      onPage={(page) => updateTab({ page })}
                      onCrop={(crop) => {
                        void edit("crop", crop);
                        setTool("select");
                      }}
                      onPrepare={() => void prepare()}
                      tool={tool}
                      onToolChange={setTool}
                    />
                  </div>
                  <SettingsPanel
                    tab={tab}
                    info={info}
                    update={updateSettings}
                    preview={preview}
                    printer={printer}
                    setPrinter={setPrinter}
                    printing={printing}
                    disabled={busy || preparing}
                    onPrint={() => void printDocument()}
                    onExport={() => void exportDocument()}
                    onDriver={driver}
                    onRefresh={() => void refresh()}
                  />
                </div>
              </>
            ) : (
              <EmptyState />
            )}
          </>
        ) : view === "merge" ? (
          <MergeView
            key={tabs.map((item) => item.id).join(",")}
            tabs={tabs}
            onOpen={() => void openDocuments()}
            onMerge={(options) => void merge(options)}
            busy={busy}
          />
        ) : view === "jobs" ? (
          <JobsView
            jobs={jobs}
            onReport={(client, print) => void report(client, print)}
            busy={busy}
          />
        ) : (
          <PreferencesView
            info={info}
            onRefresh={() => void refresh()}
            onSave={(routes) => void saveRoutes(routes)}
            onPrinter={(name, properties) => {
              void engine("printer_dialog", {
                printer: name,
                properties,
              }).catch((error) => notify(String(error), true));
            }}
            busy={busy}
          />
        )}
        <footer className="editor-statusbar">
          <span role="status">
            {busy
              ? "Procesando…"
              : preparing
                ? "Preparando vista de impresión…"
                : toast && !toast.error
                  ? toast.text
                  : tab
                    ? `${tab.selected.length} páginas seleccionadas`
                    : "Listo"}
          </span>
          <span>{tab ? `${tab.width} × ${tab.height} mm` : ""}</span>
        </footer>
        {toast?.error && (
          <div className="editor-error" role="alert">
            <AlertCircle size={17} />
            <span>{toast.text}</span>
            <button
              className="icon-button"
              aria-label="Cerrar aviso"
              onClick={() => setToast(null)}
            >
              <X size={16} />
            </button>
          </div>
        )}
      </main>
      {dragging && (
        <div className="drop-overlay">
          <div>
            <FileText size={32} />
            <h2>Soltar archivos</h2>
          </div>
        </div>
      )}
      <EditorDialogs
        help={help}
        confirm={confirm}
        count={tab?.selected.length || 0}
        busy={busy}
        onCloseHelp={() => setHelp(false)}
        onCloseConfirm={() => setConfirm(false)}
        onDelete={() => void edit("delete")}
      />
    </div>
  );
}
