"""Price estimates, submitted job history and PDF reports."""

import datetime
import json
import math
import os
import subprocess
import sys
import uuid
from pathlib import Path
from tkinter import messagebox

import pymupdf as fitz

from grafiplot.constants import PAPERS, paper_rate
from grafiplot.core.printing import build_print_command, find_sumatra


class ReportsMixin:
    def physical_sheets(self, output_sides):
        # Booklet output is always ordered front/back, two sides per sheet.
        return math.ceil(
            output_sides
            / (2 if self.mode.get() == "Folleto" or self.duplex.get() else 1)
        )

    def refresh_price(self, output_sides=None):
        if not hasattr(self, "price_label"):
            return
        if not self.document or not self.book_price.get():
            self.price_label.configure(text="")
            return
        try:
            if output_sides is None:
                number = len(self.ordered_page_ids())
                mode = self.mode.get()
                if mode == "Folleto":
                    output_sides = math.ceil(number / 4) * 2
                elif mode == "Varias páginas por hoja":
                    layout = self.nup_layout.get()
                    if layout == "Todas en una hoja":
                        nper = max(1, number)
                    elif layout == "A medida (mm, separación 5 mm)":
                        paper = PAPERS.get(self.paper.get()) or (
                            float(self.cw.get()),
                            float(self.ch.get()),
                        )
                        pw, ph = (
                            paper[::-1]
                            if self.orientation.get() == "Horizontal"
                            else paper
                        )
                        usablew = pw - 2 * float(self.margin.get())
                        usableh = ph - 2 * float(self.margin.get())
                        cellw = float(self.nup_width.get().replace(",", "."))
                        cellh = float(self.nup_height.get().replace(",", "."))
                        nper = max(
                            1,
                            int((usablew + 5) // (cellw + 5))
                            * int((usableh + 5) // (cellh + 5)),
                        )
                    elif layout == "Elegir columnas × filas":
                        nper = int(self.nup_cols.get()) * int(self.nup_rows.get())
                    else:
                        nper = int(self.per_sheet.get())
                    output_sides = math.ceil(number / max(1, nper))
                elif mode == "Póster":
                    output_sides = number * int(self.cols.get()) * int(self.rows.get())
                else:
                    output_sides = number
            sheets = self.physical_sheets(output_sides) * max(1, int(self.copies.get()))
            self.price_label.configure(
                text=f"ESTIMADO • {sheets} hojas físicas • S/ {sheets*paper_rate(self.paper.get()):.2f} (S/ {paper_rate(self.paper.get()):.2f}/hoja {self.paper.get().split()[0]})"
            )
        except Exception:
            self.price_label.configure(text="LIBRO • Revise páginas y configuración")

    def record_job(self):
        if not self.last_output or not os.path.isfile(self.last_output):
            return
        with fitz.open(self.last_output) as d:
            sides = len(d)
        sheets = self.physical_sheets(sides) * max(1, int(self.copies.get()))
        self.job_log.append(
            {
                "formato": self.paper.get(),
                "caras_pdf": sides,
                "hojas_fisicas": sheets,
                "precio_soles": round(sheets * paper_rate(self.paper.get()), 2),
                "copias": int(self.copies.get()),
                "impresora": self.printer.get(),
                "modo": self.mode.get(),
                "cliente": self.client.get(),
                "grupo": self.group_name.get(),
                "archivo": self.path.get(),
                "estado": "Enviado (no confirmado)",
            }
        )
        if self.active_tab in self.tabs_data:
            if self._skip_save_tab != self.active_tab:
                self.tabs_data[self.active_tab] = self._state()
            self._skip_save_tab = None

    def save_report_printer(self):
        chosen = self.report_printer.get()
        if chosen != "Impresora predeterminada" and chosen not in self.list_printers():
            messagebox.showwarning(
                "Impresora", "La impresora seleccionada no está disponible."
            )
            return
        self.routes["_report_printer"] = chosen
        try:
            self.config_path.write_text(
                json.dumps(self.routes, ensure_ascii=False, indent=2), encoding="utf-8"
            )
        except Exception as exc:
            messagebox.showerror("Guardar configuración", str(exc))
            return
        messagebox.showinfo("Reportes", "Impresora A4 guardada para los reportes.")

    def _report_jobs(self):
        """Aggregate jobs across opened document tabs in the active customer group."""
        group = self.group_name.get().strip()
        if not group:
            return list(self.job_log)
        jobs = list(self.job_log)
        for tab_id, state in self.tabs_data.items():
            if (
                tab_id != self.active_tab
                and state.get("group_name", "").strip() == group
            ):
                jobs.extend(state.get("job_log", []))
        jobs.extend(self.groups.get(group, []))
        return jobs

    def build_report_pdf(self, path):
        """Reporte A4 vectorial: fuente de texto PDF, sin rasterizar."""
        from collections import defaultdict

        summary = defaultdict(lambda: [0, 0, 0.0])
        for job in self._report_jobs():
            record = summary[job["formato"]]
            record[0] += 1
            record[1] += job["hojas_fisicas"]
            record[2] += job["precio_soles"]
        pdf = fitz.open()
        pg = pdf.new_page(width=595.28, height=841.89)
        W = pg.rect.width
        left = 42
        right = W - 42

        def txt(x, y, msg, size=10, font="helv", color=(0, 0, 0)):
            pg.insert_text(
                (x, y), str(msg), fontsize=size, fontname=font, color=(0, 0, 0)
            )

        def line(y):
            pg.draw_line((left, y), (right, y), color=(0, 0, 0), width=0.35)

        pg.insert_text(
            (left, 38),
            "GRAFIPLOT VASQUEZ",
            fontsize=17,
            fontname="hebo",
            color=(0, 0, 0),
        )
        txt(left, 90, "REPORTE DE IMPRESION / CONTROL INTERNO", 12, "hebo")
        txt(
            left,
            116,
            "Cliente / Pedido: "
            + (
                self.group_name.get().strip()
                or self.client.get().strip()
                or "Sin especificar"
            ),
            11,
            "hebo",
        )
        txt(left, 137, "Archivo: " + Path(self.path.get()).name[:76])
        txt(left, 157, "Fecha: " + datetime.datetime.now().strftime("%d/%m/%Y %H:%M"))
        txt(
            left,
            180,
            "Tarifas por hoja fisica: A4 0.10 | A3 0.50 | A2 1.50 | A1 2.00 | A0 4.00",
            9,
        )
        line(196)
        y = 217
        txt(left + 8, y, "FORMATO", 10, "hebo")
        txt(294, y, "TRABAJOS", 9, "hebo")
        txt(368, y, "HOJAS", 9, "hebo")
        txt(454, y, "TOTAL S/", 9, "hebo")
        y += 32
        for label, v in sorted(summary.items()):
            if y > 700:
                break
            txt(left + 8, y, label[:35], 9)
            txt(310, y, str(v[0]), 10)
            txt(382, y, str(v[1]), 10)
            txt(464, y, f"{v[2]:.2f}", 10)
            line(y + 9)
            y += 29
        if not summary:
            txt(left + 8, y, "Sin trabajos enviados desde esta pestaña.")
            y += 35
        jobs = self._report_jobs()
        totaljobs = len(jobs)
        sheets = sum(j["hojas_fisicas"] for j in jobs)
        cost = sum(j["precio_soles"] for j in jobs)
        y = max(y + 18, 600)
        txt(left, y, f"TRABAJOS ENVIADOS: {totaljobs}", 11, "hebo")
        txt(left, y + 23, f"HOJAS FISICAS ESTIMADAS: {sheets}", 11, "hebo")
        txt(left, y + 48, f"IMPORTE REFERENCIAL: S/ {cost:.2f}", 13, "hebo")
        line(757)
        txt(left, 775, "Estado: ENVIADO / REGISTRADO. No confirma impresion fisica.", 8)
        txt(
            left,
            790,
            "Resumen por cliente/grupo. Trabajos enviados (no confirmados).",
            8,
        )
        pdf.save(path, garbage=3, deflate=True)
        pdf.close()
        return path

    def report_tab(self):
        """Imprime directamente reporte A4 en la impresora específica de reportes."""
        if not self.document:
            return messagebox.showinfo("Reporte", "Abra un archivo primero.")

        path = os.path.join(self.tmp.name, "reporte_A4_" + uuid.uuid4().hex + ".pdf")
        try:
            self.build_report_pdf(path)
        except Exception as exc:
            return messagebox.showerror("Reporte", str(exc))
        if sys.platform != "win32":
            return messagebox.showinfo(
                "Reporte creado",
                f"Reporte temporal A4: {path}\nLa impresión automática requiere Windows.",
            )
        printer = self.report_printer.get()
        exe = find_sumatra()
        if not exe:
            return messagebox.showerror(
                "Imprimir reporte",
                "Instale SumatraPDF para imprimir directamente el reporte A4.",
            )
        try:
            subprocess.Popen(build_print_command(exe, path, printer, scale="fit"))
            messagebox.showinfo(
                "Reporte enviado",
                f"Reporte A4 enviado a {printer}. No confirma impresión física.",
            )
        except Exception as exc:
            messagebox.showerror("Imprimir reporte", str(exc))
