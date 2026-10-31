"""Document sessions and validated commands for the React desktop."""

import base64
import datetime
import json
import os
import subprocess
from pathlib import Path

import pymupdf as fitz

from grafiplot.constants import PAPERS
from grafiplot.core.external import system_dll_search, system_environment
from grafiplot.core.printing import DEFAULT_PRINTER, build_print_command, find_sumatra
from grafiplot.desktop.printer_support import (
    error_reason,
    printer_details,
    process_text,
    write_diagnostic,
)


class PrintingMixin:
    def _submit_print(self, executable, path, printer, settings):
        with system_dll_search():
            details = printer_details(printer)
        actual_printer = details["name"]
        duplex = bool(settings.get("duplex") or settings.get("mode") == "booklet")
        if duplex and details["duplex"] is False:
            raise ValueError(
                f"El controlador de «{actual_printer}» informa que no admite doble cara automática. Revise sus propiedades o elija «Una cara». No se envió la solicitud."
            )
        command = build_print_command(
            executable,
            path,
            actual_printer,
            settings.get("paper", "A4").split(" ")[0],
            settings.get("copies", 1),
            duplex,
            settings.get("mode") == "booklet",
            settings.get("_print_scale", "noscale"),
        )
        record = {
            "printer": actual_printer,
            "paper": settings.get("paper", "A4"),
            "duplex": duplex,
            "copies": settings.get("copies", 1),
            "printer_details": details,
            "command": command,
        }
        flags = (
            {"creationflags": subprocess.CREATE_NO_WINDOW} if os.name == "nt" else {}
        )
        try:
            with system_dll_search():
                result = subprocess.run(
                    command,
                    capture_output=True,
                    timeout=180,
                    env=system_environment(),
                    **flags,
                )
        except subprocess.TimeoutExpired as error:
            log = write_diagnostic(
                self.log_directory,
                {**record, "timeout": True, "stderr": process_text(error.stderr)},
            )
            raise RuntimeError(
                f"No se confirmó el envío a «{actual_printer}» en 180 segundos. Revise la cola antes de repetir para evitar duplicados."
                + (f" Registro: {log}" if log else "")
            ) from error
        except OSError as error:
            log = write_diagnostic(
                self.log_directory, {**record, "launch_error": str(error)}
            )
            raise RuntimeError(
                f"No se pudo iniciar SumatraPDF para «{actual_printer}»: {error}."
                + (f" Registro: {log}" if log else "")
            ) from error
        if result.returncode:
            log = write_diagnostic(
                self.log_directory,
                {
                    **record,
                    "returncode": result.returncode,
                    "status_hex": f"0x{result.returncode & 0xffffffff:08X}",
                    "stdout": process_text(result.stdout),
                    "stderr": process_text(result.stderr),
                },
            )
            message = f"Impresora «{actual_printer}» · Código {result.returncode} (0x{result.returncode & 0xffffffff:08X}). {error_reason(result.returncode)} Revise la cola antes de repetir."
            raise RuntimeError(message + (f" Registro: {log}" if log else ""))
        return actual_printer

    def info(self):
        routes = {}
        try:
            routes = json.loads(self.config_path.read_text(encoding="utf-8"))
            if not isinstance(routes, dict):
                routes = {}
        except (OSError, ValueError):
            pass
        printers = [DEFAULT_PRINTER]
        default_printer = None
        if os.name == "nt":
            try:
                import win32print

                printers += sorted({p[2] for p in win32print.EnumPrinters(6)})
                try:
                    default_printer = win32print.GetDefaultPrinter()
                except Exception:
                    pass
            except ImportError:
                pass
        return {
            "papers": PAPERS,
            "printers": printers,
            "routes": routes,
            "sumatra": bool(find_sumatra()),
            "defaultPrinter": default_printer,
        }

    def save_routes(self, routes):
        if not isinstance(routes, dict) or not all(
            isinstance(k, str) and isinstance(v, str) for k, v in routes.items()
        ):
            raise ValueError("Asignaciones de impresora inválidas.")
        self.config_path.write_text(
            json.dumps(routes, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        return True

    def print_document(self, document_id, settings, printer=DEFAULT_PRINTER, client=""):
        executable = find_sumatra()
        if not executable:
            raise ValueError(
                "Instale SumatraPDF para imprimir directamente. Puede exportar el PDF mientras tanto."
            )
        result = self.prepare(document_id, settings)
        output = self.previews[document_id]["path"]
        # A separate copy survives subsequent preview regeneration while Sumatra reads it.
        import shutil

        print_copy = self._path()
        shutil.copyfile(output, print_copy)
        printer = self._submit_print(executable, print_copy, printer, settings)
        self.jobs.append(
            {
                "client": client,
                "name": self._document(document_id)["name"],
                "printer": printer,
                "paper": settings.get("paper", "A4"),
                "sheets": result["sheets"],
                "cost": result["cost"],
                "copies": settings.get("copies", 1),
                "date": datetime.datetime.now().isoformat(timespec="seconds"),
            }
        )
        return {
            **result,
            "selected": self.previews[document_id]["indexes"],
            "jobs": self.jobs,
        }

    def report(self, client="", path=None, printer=None):
        jobs = [job for job in self.jobs if not client or job["client"] == client]
        target = self._path()
        with fitz.open() as pdf:
            page = None
            y = 0
            for index, job in enumerate(jobs or [None]):
                if page is None or y > 720:
                    page = pdf.new_page(width=595, height=842)
                    page.insert_text(
                        (42, 52),
                        "GRAFIPLOT / REPORTE DE IMPRESION",
                        fontsize=17,
                        fontname="hebo",
                    )
                    page.insert_text(
                        (42, 78), "Cliente: " + (client or "Todos"), fontsize=11
                    )
                    y = 115
                text = (
                    f"{index+1}. {job['name'][:48]} | {job['sheets']} hojas | S/ {job['cost']:.2f}"
                    if job
                    else "No hay trabajos enviados para este cliente."
                )
                page.insert_text((42, y), text, fontsize=10)
                y += 27
            page.insert_text(
                (42, y + 25),
                f"TOTAL: {sum(j['sheets'] for j in jobs)} hojas / S/ {sum(j['cost'] for j in jobs):.2f}",
                fontsize=13,
                fontname="hebo",
            )
            page.insert_text(
                (42, 798), "Trabajos enviados. No confirma salida fisica.", fontsize=9
            )
            pdf.save(target)
        if printer:
            executable = find_sumatra()
            if not executable:
                raise ValueError("Se necesita SumatraPDF para imprimir el reporte.")
            self._submit_print(
                executable, target, printer, {"paper": "A4", "_print_scale": "fit"}
            )
            return {"printed": True}
        if path:
            target_path = self._safe_target(path)
            with open(target_path, "xb") as stream:
                stream.write(Path(target).read_bytes())
            return {"path": str(target_path)}
        return {"data": base64.b64encode(Path(target).read_bytes()).decode("ascii")}

    def printer_dialog(self, printer, properties=False):
        if os.name != "nt":
            raise ValueError("Disponible únicamente en Windows.")
        if printer == DEFAULT_PRINTER:
            import win32print

            printer = win32print.GetDefaultPrinter()
        with system_dll_search():
            subprocess.Popen(
                [
                    "rundll32.exe",
                    "printui.dll,PrintUIEntry",
                    "/p" if properties else "/e",
                    "/n",
                    printer,
                ],
                env=system_environment(),
            )
        return True
