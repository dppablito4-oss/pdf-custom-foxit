"""Run `python -m scripts.preview_ui` to inspect the UI with synthetic documents."""

import tempfile
from pathlib import Path

import pymupdf as fitz

from grafiplot.application import App


def main():
    with tempfile.TemporaryDirectory(prefix="grafiplot_preview_") as folder:
        path = Path(folder) / "Muestra de impresión.pdf"
        with fitz.open() as document:
            for number in range(1, 5):
                page = document.new_page(width=595, height=842)
                page.draw_rect((0, 0, 595, 12), fill=(0.71, 0.12, 0.22), color=None)
                page.insert_text(
                    (48, 78),
                    "GRAFIPLOT",
                    fontsize=30,
                    fontname="hebo",
                    color=(0.71, 0.12, 0.22),
                )
                page.insert_text(
                    (48, 104),
                    "ESTUDIO DE IMPRESION",
                    fontsize=10,
                    color=(0.4, 0.44, 0.5),
                )
                page.draw_line((48, 132), (547, 132), color=(0.85, 0.88, 0.91))
                page.insert_text(
                    (48, 185),
                    f"Documento de muestra / {number:02}",
                    fontsize=23,
                    fontname="hebo",
                )
                page.insert_text(
                    (48, 215),
                    "Texto y graficos vectoriales listos para imprimir.",
                    fontsize=12,
                )
                for row in range(3):
                    y = 260 + row * 115
                    page.draw_rect(
                        (48, y, 547, y + 88), fill=(0.95, 0.96, 0.98), color=None
                    )
                    page.insert_text(
                        (66, y + 28), f"Seccion {row+1}", fontsize=13, fontname="hebo"
                    )
                    page.insert_text(
                        (66, y + 53),
                        "Vista previa, seleccion de paginas y configuracion de salida.",
                        fontsize=11,
                    )
                page.insert_text(
                    (48, 785),
                    f"MUESTRA DE DESARROLLO                                     PAGINA {number} / 4",
                    fontsize=9,
                )
            document.save(path)
        app = App()
        app.after(200, lambda: app.open_paths([str(path)]))
        app.mainloop()


if __name__ == "__main__":
    main()
