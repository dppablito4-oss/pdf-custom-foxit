"""Windows printer configuration, export and job submission."""

import json
import os
import subprocess
import sys
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from grafiplot.core.layout import create_output
from grafiplot.core.printing import build_print_command, find_sumatra


class PrintingMixin:
    def auto_printer(self):
        name = self.routes.get(self.paper.get())
        if name:
            available = self.list_printers()
            if name in available:
                self.printer.set(name)

    def list_printers(self):
        if sys.platform != "win32":
            return []
        try:
            import win32print

            return sorted(
                set(
                    p[2]
                    for p in win32print.EnumPrinters(
                        win32print.PRINTER_ENUM_LOCAL
                        | win32print.PRINTER_ENUM_CONNECTIONS
                    )
                )
            )
        except Exception:
            return []

    def assign_printer(self):
        name = self.printer.get()
        if name == "Impresora predeterminada":
            return messagebox.showwarning(
                "Asignación", "Seleccione una impresora instalada."
            )
        self.routes[self.paper.get()] = name
        try:
            self.config_path.write_text(
                json.dumps(self.routes, ensure_ascii=False, indent=2), encoding="utf-8"
            )
        except Exception as e:
            return messagebox.showerror("Guardar configuración", str(e))
        messagebox.showinfo(
            "Asignación guardada",
            f"{self.paper.get()} → {name}\nEsta selección será automática al elegir el papel.",
        )

    def printer_preferences(self):
        self._windows_printer_dialog("/e")

    def printer_properties(self):
        self._windows_printer_dialog("/p")

    def _windows_printer_dialog(self, flag):
        if sys.platform != "win32":
            return messagebox.showinfo(
                "Windows", "Disponible al ejecutar el programa en Windows."
            )
        name = self.printer.get()
        if name == "Impresora predeterminada":
            try:
                import win32print

                name = win32print.GetDefaultPrinter()
            except Exception:
                return messagebox.showwarning(
                    "Impresora", "Seleccione una impresora de la lista."
                )
        try:
            subprocess.Popen(
                ["rundll32.exe", "printui.dll,PrintUIEntry", flag, "/n", name]
            )
        except Exception as e:
            messagebox.showerror("Ajustes de impresora", str(e))

    def export(self):
        if not self.source:
            messagebox.showwarning(
                "Archivo requerido", "Primero seleccione un archivo."
            )
            return None
        try:
            job_source, args, job_pages = self.selected_source()
        except Exception as e:
            messagebox.showerror("Configuración", str(e))
            return None
        path = filedialog.asksaveasfilename(
            title="Guardar PDF listo para imprimir",
            defaultextension=".pdf",
            initialfile=Path(self.path.get()).stem + "_GRAFIPLOT_PRINT.pdf",
            filetypes=[("PDF", "*.pdf")],
        )
        if not path:
            return None
        try:
            count = create_output(job_source, path, *args)
            self.last_output = path
            self.last_export_pages = job_pages.copy()
            messagebox.showinfo(
                "PDF preparado",
                f"Archivo creado correctamente.\n{count} página(s) para impresión.\n\n{path}\n\nAl imprimir seleccione tamaño real / 100%, NO «Ajustar».",
            )
            return path
        except Exception as e:
            messagebox.showerror("Error al generar PDF", str(e))
            return None

    def refresh_printers(self):
        printers = ["Impresora predeterminada"] + self.list_printers()

        def crawl(root):
            for item in root.winfo_children():
                if isinstance(item, ttk.Combobox) and item.cget("textvariable") in (
                    str(self.printer),
                    str(self.report_printer),
                ):
                    item["values"] = printers
                crawl(item)

        crawl(self)
        self.auto_printer()

    def print_file(self):
        """Prepara un PDF temporal nuevo en cada clic y lo envía sin solicitar Guardar."""
        if not self.source:
            return messagebox.showwarning(
                "Archivo requerido", "Abra un documento primero."
            )
        if sys.platform != "win32":
            return messagebox.showwarning(
                "Solo Windows",
                "La impresión directa requiere Windows y una impresora instalada. Puede guardar el PDF preparado.",
            )
        try:
            job_source, args, job_pages = self.selected_source()
            # Cada impresión se prepara desde la configuración ACTUAL, incluso si antes se imprimió.
            import uuid

            output = os.path.join(
                self.tmp.name, "impresion_" + uuid.uuid4().hex + ".pdf"
            )
            count = create_output(job_source, output, *args)
            if count < 1:
                raise RuntimeError("No hay páginas que imprimir.")
            exe = find_sumatra()
            printer = self.printer.get()
            if not exe:
                raise RuntimeError(
                    "Para la impresión directa instale SumatraPDF mediante INSTALAR_TODO_WINDOWS.bat. No se envió ningún trabajo."
                )
            paper_name = self.paper.get().split(" ", 1)[0]
            # Folleto siempre doble cara; la configuración de borde corto puede variar según controlador.
            copies = int(self.copies.get())
            command = build_print_command(
                exe,
                output,
                printer,
                paper_name,
                copies,
                self.duplex.get(),
                self.mode.get() == "Folleto",
            )
            subprocess.Popen(command)
            self.last_output = output
            self.last_export_pages = set(job_pages)
            self.sent_pages.update(job_pages)
            self.refresh_selection()
            self.record_job()
            messagebox.showinfo(
                "Trabajo enviado",
                f"Se envió la solicitud de {count} cara(s) × {copies} copia(s) a {printer}.\n\nPuede volver a seleccionar e imprimir las páginas verdes.\n\nEl color verde indica ENVIADO, no salida física confirmada.",
            )
        except Exception as exc:
            messagebox.showerror("No se pudo imprimir", str(exc))
