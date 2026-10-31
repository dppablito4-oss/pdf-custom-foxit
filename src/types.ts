export type Mode = "normal" | "poster" | "booklet" | "nup";
export type View = "studio" | "merge" | "jobs" | "preferences";
export interface DocumentInfo {
  id: string;
  name: string;
  pages: number;
  size: number;
  width: number;
  height: number;
  revision: number;
}
export interface PrintSettings {
  mode: Mode;
  paper: string;
  orientation: "portrait" | "landscape";
  margin: number;
  overlap: number;
  columns: number;
  rows: number;
  copies: number;
  duplex: boolean;
  content: number;
  autorotate: boolean;
  scale: string;
  perSheet: number;
  layout: string;
  nupColumns: number;
  nupRows: number;
  cellWidth: number;
  cellHeight: number;
  center: boolean;
  order: string;
  excluded: string;
  selectionOnly: boolean;
  selected: number[];
  paperWidth: number;
  paperHeight: number;
}
export interface DocumentTab extends DocumentInfo {
  settings: PrintSettings;
  selected: number[];
  sent: number[];
  page: number;
  client: string;
}
export interface EngineInfo {
  defaultPrinter?: string | null;
  papers: Record<string, [number, number] | null>;
  printers: string[];
  routes: Record<string, string>;
  sumatra: boolean;
}
export interface PreviewInfo {
  pages: number;
  sheets: number;
  cost: number;
  width: number;
  height: number;
}
export interface Job {
  client: string;
  name: string;
  printer: string;
  paper: string;
  sheets: number;
  cost: number;
  copies: number;
  date: string;
}
export const DEFAULT_PRINTER = "Impresora predeterminada";
export const defaultSettings = (): PrintSettings => ({
  mode: "normal",
  paper: "A4 (210 × 297 mm)",
  orientation: "portrait",
  margin: 5,
  overlap: 5,
  columns: 2,
  rows: 2,
  copies: 1,
  duplex: false,
  content: 100,
  autorotate: true,
  scale: "Ajustar",
  perSheet: 2,
  layout: "auto",
  nupColumns: 2,
  nupRows: 2,
  cellWidth: 50,
  cellHeight: 70,
  center: true,
  order: "",
  excluded: "",
  selectionOnly: false,
  selected: [],
  paperWidth: 210,
  paperHeight: 297,
});
