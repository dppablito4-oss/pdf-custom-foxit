import { invoke, isTauri } from "@tauri-apps/api/core";
import { open, save } from "@tauri-apps/plugin-dialog";
import type { DocumentInfo } from "../types";

export const desktop = isTauri();

export async function engine<T>(
  method: string,
  params: Record<string, unknown> = {},
): Promise<T> {
  const request = { method, params };
  const response: { result?: T; error?: string } = desktop
    ? await invoke("engine", { request })
    : await fetch("/api/engine", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(request),
      }).then(async (response) => {
        if (!response.ok)
          throw new Error("No se pudo conectar con el motor PDF local.");
        return response.json();
      });
  if (response.error) throw new Error(response.error);
  return response.result as T;
}

export type OpenResult = { documents: DocumentInfo[]; errors: string[] };
export async function chooseDocuments(): Promise<OpenResult | null> {
  if (desktop) {
    const paths = await open({
      multiple: true,
      title: "Abrir documentos",
      filters: [
        {
          name: "Documentos e imágenes",
          extensions: [
            "pdf",
            "png",
            "jpg",
            "jpeg",
            "tif",
            "tiff",
            "bmp",
            "webp",
            "gif",
            "doc",
            "docx",
            "xls",
            "xlsx",
            "ppt",
            "pptx",
            "odt",
            "ods",
            "odp",
            "rtf",
            "txt",
            "svg",
            "zip",
            "rar",
          ],
        },
      ],
    });
    if (!paths) return null;
    return engine("open", { paths: Array.isArray(paths) ? paths : [paths] });
  }
  const input = document.createElement("input");
  input.type = "file";
  input.multiple = true;
  input.accept =
    ".pdf,.png,.jpg,.jpeg,.tif,.tiff,.bmp,.webp,.gif,.doc,.docx,.xls,.xlsx,.ppt,.pptx,.odt,.ods,.odp,.rtf,.txt,.svg,.zip,.rar";
  const files = await new Promise<File[]>((resolve) => {
    input.onchange = () => resolve(Array.from(input.files || []));
    input.oncancel = () => resolve([]);
    input.click();
  });
  return files.length ? uploadDocuments(files) : null;
}

export async function uploadDocuments(files: File[]): Promise<OpenResult> {
  const encoded = await Promise.all(
    files.map(async (file) => ({
      name: file.name,
      data: await new Promise<string>((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => resolve(String(reader.result).split(",")[1]);
        reader.onerror = reject;
        reader.readAsDataURL(file);
      }),
    })),
  );
  return engine("upload", { files: encoded });
}

export async function savePath(
  name: string,
): Promise<string | null | undefined> {
  if (!desktop) return undefined;
  return save({
    title: "Guardar PDF",
    defaultPath: name,
    filters: [{ name: "PDF", extensions: ["pdf"] }],
  });
}
export function downloadPdf(data: string, name: string) {
  const bytes = Uint8Array.from(atob(data), (char) => char.charCodeAt(0));
  const url = URL.createObjectURL(
    new Blob([bytes], { type: "application/pdf" }),
  );
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = name;
  anchor.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
