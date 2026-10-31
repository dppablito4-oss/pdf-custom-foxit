"""Browser integration against Vite and real Python PDF processing."""

import json
import tempfile
from pathlib import Path

from playwright.sync_api import sync_playwright

from tests.test_core import sample_pdf


def main():
    artifacts = Path("artifacts/screenshots")
    artifacts.mkdir(parents=True, exist_ok=True)
    with (
        tempfile.TemporaryDirectory(prefix="grafiplot_web_") as folder,
        sync_playwright() as playwright,
    ):
        first = sample_pdf(Path(folder) / "Proyecto editorial.pdf", 5)
        second = sample_pdf(Path(folder) / "Laminas de muestra.pdf", 2)
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page(
            viewport={"width": 1440, "height": 1000}, device_scale_factor=1
        )
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto("http://127.0.0.1:1420")
        page.get_by_text("Sin documento", exact=True).first.wait_for()
        page.screenshot(path=str(artifacts / "01-inicio.png"))
        with page.expect_file_chooser() as chooser:
            page.get_by_role("button", name="Abrir documentos", exact=True).click()
        chooser.value.set_files(first)
        page.get_by_role("img", name="Vista original, página 1").wait_for(timeout=30000)
        page.get_by_text("S/ 0.50", exact=True).wait_for(timeout=30000)
        page.screenshot(path=str(artifacts / "02-estudio.png"))
        page.get_by_label("Modo de impresión", exact=True).select_option("poster")
        page.get_by_text("S/ 2.00", exact=True).wait_for(timeout=30000)
        page.get_by_role("button", name="Impresión", exact=True).click()
        page.get_by_role("img", name="Vista de impresión, página 1").wait_for()
        page.screenshot(path=str(artifacts / "03-poster.png"))
        page.get_by_label("Modo de impresión", exact=True).select_option("booklet")
        page.get_by_text("S/ 0.20", exact=True).wait_for(timeout=30000)
        page.get_by_label("Modo de impresión", exact=True).select_option("normal")
        page.get_by_role("button", name="Página 1", exact=True).click()
        page.get_by_role("button", name="Página 3", exact=True).click(
            modifiers=["Control"]
        )
        page.get_by_text("2 seleccionadas", exact=True).wait_for()
        page.get_by_role("button", name="Girar selección", exact=True).click()
        page.get_by_role("status").filter(has_text="Páginas giradas.").wait_for()
        with page.expect_download() as download:
            page.get_by_role("button", name="Guardar PDF", exact=True).click()
        download.value.save_as(str(Path(folder) / "exported.pdf"))
        assert (Path(folder) / "exported.pdf").stat().st_size > 100
        with page.expect_file_chooser() as chooser:
            page.get_by_role("button", name="Abrir documentos", exact=True).click()
        chooser.value.set_files(second)
        page.get_by_role("img", name="Vista original, página 1").wait_for()
        page.get_by_role("button", name="Combinar PDF", exact=True).click()
        page.get_by_role("heading", name="Combinar documentos", exact=True).wait_for()
        page.screenshot(path=str(artifacts / "04-combinar.png"))
        page.get_by_role("button", name="Combinar y abrir PDF", exact=True).click()
        page.get_by_text("Combinado.pdf", exact=True).first.wait_for(timeout=30000)
        page.get_by_role("button", name="Trabajos enviados", exact=True).click()
        page.get_by_role("heading", name="Trabajos enviados", exact=True).wait_for()
        page.get_by_role("button", name="Preferencias", exact=True).click()
        page.get_by_role(
            "heading", name="Preferencias de impresión", exact=True
        ).wait_for()
        page.screenshot(path=str(artifacts / "05-preferencias.png"))
        page.get_by_role("button", name="Documentos", exact=True).click()
        page.set_viewport_size({"width": 1060, "height": 740})
        page.wait_for_timeout(700)
        assert page.evaluate(
            "document.documentElement.scrollWidth <= window.innerWidth"
        )
        page.screenshot(path=str(artifacts / "06-compacto.png"))
        if errors:
            raise AssertionError(json.dumps(errors))
        browser.close()
    print(
        "Web smoke OK: apertura, miniaturas, modos, selección, giro, exportación, combinación, preferencias y ventana compacta."
    )


if __name__ == "__main__":
    main()
