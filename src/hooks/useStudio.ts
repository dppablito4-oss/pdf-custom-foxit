import { useCallback, useEffect, useRef, useState } from "react";
import { invoke } from "@tauri-apps/api/core";
import { getCurrentWebviewWindow } from "@tauri-apps/api/webviewWindow";
import type { View } from "../types";
import type { MergeOptions } from "../components/SecondaryViews";
import {
  chooseDocuments,
  desktop,
  downloadPdf,
  engine,
  savePath,
  uploadDocuments,
  type OpenResult,
} from "../lib/engine";
import {
  DEFAULT_PRINTER,
  defaultSettings,
  type DocumentInfo,
  type DocumentTab,
  type EngineInfo,
  type Job,
  type PreviewInfo,
  type PrintSettings,
} from "../types";

export function useStudio() {
  const [view, setView] = useState<View>("studio"),
    [tabs, setTabs] = useState<DocumentTab[]>([]),
    [active, setActive] = useState(""),
    [info, setInfo] = useState<EngineInfo>({
      papers: { "A4 (210 × 297 mm)": [210, 297] },
      printers: [DEFAULT_PRINTER],
      routes: {},
      sumatra: false,
    }),
    [printer, setPrinter] = useState(DEFAULT_PRINTER),
    [busy, setBusy] = useState(false),
    [printing, setPrinting] = useState(false),
    [preparing, setPreparing] = useState(false),
    [preview, setPreview] = useState<PreviewInfo | null>(null),
    [previewVersion, setPreviewVersion] = useState(0),
    [jobs, setJobs] = useState<Job[]>([]),
    [toast, setToast] = useState<{ text: string; error?: boolean } | null>(
      null,
    ),
    [help, setHelp] = useState(false),
    [confirm, setConfirm] = useState(false),
    [dragging, setDragging] = useState(false);
  const tab = tabs.find((tab) => tab.id === active),
    anchor = useRef(0),
    prepareGeneration = useRef(0),
    initialized = useRef(false);
  const notify = useCallback(
    (text: string, error = false) => setToast({ text, error }),
    [],
  );
  useEffect(() => {
    if (!toast || toast.error) return;
    const timer = setTimeout(() => setToast(null), toast.error ? 10000 : 5000);
    return () => clearTimeout(timer);
  }, [toast]);
  const addDocuments = useCallback(
    (result: OpenResult) => {
      if (result.documents.length) {
        setTabs((tabs) => [
          ...tabs,
          ...result.documents.map((doc) => ({
            ...doc,
            settings: defaultSettings(),
            selected: [],
            sent: [],
            page: 0,
            client: "",
          })),
        ]);
        setActive(result.documents.at(-1)!.id);
        setPreview(null);
        setView("studio");
        notify(
          `${result.documents.length} documento${result.documents.length === 1 ? "" : "s"} abierto${result.documents.length === 1 ? "" : "s"}.`,
        );
      }
      if (result.errors.length) notify(result.errors.join("\n"), true);
    },
    [notify],
  );
  const openDocuments = useCallback(async () => {
    setBusy(true);
    try {
      const result = await chooseDocuments();
      if (result) addDocuments(result);
    } catch (error) {
      notify(String(error), true);
    } finally {
      setBusy(false);
    }
  }, [addDocuments, notify]);
  const refresh = useCallback(async () => {
    try {
      setInfo(await engine<EngineInfo>("info"));
    } catch (error) {
      notify(String(error), true);
    }
  }, [notify]);
  useEffect(() => {
    if (initialized.current) return;
    initialized.current = true;
    void refresh();
    if (desktop)
      void invoke<string[]>("launch_files")
        .then((paths) =>
          paths.length
            ? engine<OpenResult>("open", { paths }).then(addDocuments)
            : null,
        )
        .catch((error) => notify(String(error), true));
  }, [refresh, addDocuments, notify]);
  useEffect(() => {
    if (!desktop) return;
    let cancelled = false;
    let cleanup: (() => void) | undefined;
    void getCurrentWebviewWindow()
      .onDragDropEvent(async (event) => {
        if (event.payload.type === "over") setDragging(true);
        else if (event.payload.type === "leave") setDragging(false);
        else if (event.payload.type === "drop") {
          setDragging(false);
          setBusy(true);
          try {
            addDocuments(
              await engine<OpenResult>("open", { paths: event.payload.paths }),
            );
          } catch (error) {
            notify(String(error), true);
          } finally {
            setBusy(false);
          }
        }
      })
      .then((unlisten) => {
        if (cancelled) unlisten();
        else cleanup = unlisten;
      });
    return () => {
      cancelled = true;
      cleanup?.();
    };
  }, [addDocuments, notify]);
  function updateTab(patch: Partial<DocumentTab>) {
    setTabs((tabs) =>
      tabs.map((t) => (t.id === active ? { ...t, ...patch } : t)),
    );
  }
  function updateSettings(patch: Partial<PrintSettings>) {
    if (!tab) return;
    updateTab({ settings: { ...tab.settings, ...patch } });
    setPreview(null);
  }
  const settingsKey = tab
    ? JSON.stringify({ ...tab.settings, selected: tab.selected })
    : "";
  const prepare = useCallback(async () => {
    if (!tab) return;
    const generation = ++prepareGeneration.current;
    setPreparing(true);
    try {
      const result = await engine<PreviewInfo>("prepare", {
        document_id: tab.id,
        settings: { ...tab.settings, selected: tab.selected },
      });
      if (generation === prepareGeneration.current) {
        setPreview(result);
        setPreviewVersion((v) => v + 1);
      }
    } catch (error) {
      if (generation === prepareGeneration.current) {
        setPreview(null);
        notify(String(error), true);
      }
    } finally {
      if (generation === prepareGeneration.current) setPreparing(false);
    }
    // Settings key describes precisely the editable state; source revision triggers after edits.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [active, settingsKey, tab?.revision, notify]);
  useEffect(() => {
    prepareGeneration.current++;
    setPreview(null);
    setPreparing(false);
    if (!tab) return;
    const timer = setTimeout(() => void prepare(), 650);
    return () => {
      clearTimeout(timer);
      prepareGeneration.current++;
    };
  }, [prepare]);
  useEffect(() => {
    const assigned = tab && info.routes[tab.settings.paper];
    if (assigned && info.printers.includes(assigned)) setPrinter(assigned);
  }, [tab?.settings.paper, info]);
  async function closeTab(id: string) {
    try {
      await engine("close", { document_id: id });
      setTabs((tabs) => tabs.filter((t) => t.id !== id));
      if (active === id) {
        setActive(tabs.filter((t) => t.id !== id).at(-1)?.id || "");
        setPreview(null);
      }
    } catch (error) {
      notify(String(error), true);
    }
  }
  const exportDocument = useCallback(async () => {
    if (!tab) return;
    const name = tab.name.replace(/\.[^.]+$/, "") + "_GRAFIPLOT.pdf";
    const path = await savePath(name);
    if (path === null) return;
    setBusy(true);
    try {
      const result = await engine<{ data?: string; path?: string }>("export", {
        document_id: tab.id,
        settings: { ...tab.settings, selected: tab.selected },
        path,
      });
      if (result.data) downloadPdf(result.data, name);
      notify("PDF preparado y guardado.");
    } catch (error) {
      notify(String(error), true);
    } finally {
      setBusy(false);
    }
  }, [tab, notify]);
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.ctrlKey && e.key.toLowerCase() === "o") {
        e.preventDefault();
        if (!busy) void openDocuments();
      } else if (e.ctrlKey && e.key.toLowerCase() === "s") {
        e.preventDefault();
        if (!busy) void exportDocument();
      } else if (e.ctrlKey && e.key === "Tab") {
        e.preventDefault();
        if (tabs.length) {
          const index = tabs.findIndex((t) => t.id === active);
          setActive(
            tabs[(index + (e.shiftKey ? -1 : 1) + tabs.length) % tabs.length]
              .id,
          );
        }
      } else if (e.key === "Escape") {
        setHelp(false);
        setConfirm(false);
      } else if (e.key === "Delete" && tab?.selected.length && !busy) {
        const target = e.target as HTMLElement;
        if (
          !["INPUT", "TEXTAREA", "SELECT"].includes(target.tagName) &&
          !target.isContentEditable
        ) {
          e.preventDefault();
          setConfirm(true);
        }
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [busy, openDocuments, exportDocument, tabs, active]);
  async function edit(action: string, crop?: number[], degrees = 90) {
    if (!tab) return;
    setBusy(true);
    try {
      const result = await engine<DocumentInfo>("edit", {
        document_id: tab.id,
        action,
        pages: tab.selected,
        crop,
        degrees,
      });
      updateTab({
        ...result,
        selected: [],
        sent: [],
        page: Math.min(tab.page, result.pages - 1),
        settings: {
          ...tab.settings,
          selectionOnly: false,
          order: "",
          excluded: "",
        },
      });
      setPreview(null);
      notify(
        action === "delete"
          ? "Páginas quitadas de la copia de trabajo."
          : action === "crop"
            ? "Recorte aplicado. Original intacto."
            : action === "clear_crop"
              ? "Recortes eliminados."
              : "Páginas giradas.",
      );
    } catch (error) {
      notify(String(error), true);
    } finally {
      setBusy(false);
      setConfirm(false);
    }
  }
  async function printDocument() {
    if (!tab) return;
    setPrinting(true);
    setBusy(true);
    try {
      const result = await engine<{ jobs: Job[]; selected: number[] }>(
        "print",
        {
          document_id: tab.id,
          settings: { ...tab.settings, selected: tab.selected },
          printer,
          client: tab.client,
        },
      );
      setJobs(result.jobs);
      updateTab({ sent: [...new Set([...tab.sent, ...result.selected])] });
      notify("Solicitud enviada a la impresora. Puedes seguir trabajando.");
    } catch (error) {
      notify(String(error), true);
    } finally {
      setPrinting(false);
      setBusy(false);
    }
  }
  async function merge(options: MergeOptions) {
    setBusy(true);
    try {
      const doc = await engine<DocumentInfo>(
        "merge",
        options as unknown as Record<string, unknown>,
      );
      addDocuments({ documents: [doc], errors: [] });
    } catch (error) {
      notify(String(error), true);
    } finally {
      setBusy(false);
    }
  }
  async function report(client: string, print = false) {
    const path = print ? undefined : await savePath("Reporte_GRAFIPLOT.pdf");
    if (path === null) return;
    setBusy(true);
    try {
      const result = await engine<{ data?: string }>("report", {
        client,
        path,
        printer: print
          ? info.routes._report_printer || DEFAULT_PRINTER
          : undefined,
      });
      if (result.data) downloadPdf(result.data, "Reporte_GRAFIPLOT.pdf");
      notify(print ? "Reporte enviado." : "Reporte guardado.");
    } catch (error) {
      notify(String(error), true);
    } finally {
      setBusy(false);
    }
  }
  async function saveRoutes(routes: Record<string, string>) {
    setBusy(true);
    try {
      await engine("save_routes", { routes });
      setInfo({ ...info, routes });
      notify("Asignaciones guardadas.");
    } catch (error) {
      notify(String(error), true);
    } finally {
      setBusy(false);
    }
  }
  async function browserDrop(e: React.DragEvent) {
    e.preventDefault();
    setDragging(false);
    if (desktop || !e.dataTransfer.files.length) return;
    setBusy(true);
    try {
      addDocuments(await uploadDocuments(Array.from(e.dataTransfer.files)));
    } catch (error) {
      notify(String(error), true);
    } finally {
      setBusy(false);
    }
  }
  return {
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
  };
}
