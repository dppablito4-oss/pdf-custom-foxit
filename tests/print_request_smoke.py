"""Intercept the final print request: verify the chosen printer without printing."""

import tempfile
from pathlib import Path

from playwright.sync_api import sync_playwright

from tests.test_core import sample_pdf


def main():
    with (
        tempfile.TemporaryDirectory(prefix="grafiplot_print_request_") as folder,
        sync_playwright() as pw,
    ):
        source = sample_pdf(Path(folder) / "Prueba A4 duplex.pdf", 2)
        browser = pw.chromium.launch(headless=True)
        page = browser.new_page()
        sent = []

        def intercept(route):
            request = route.request.post_data_json
            if request["method"] == "info":
                route.fulfill(
                    json={
                        "result": {
                            "papers": {"A4 (210 × 297 mm)": [210, 297]},
                            "printers": [
                                "Impresora predeterminada",
                                "Ruta automática A4",
                                "HP elegida por usuario",
                            ],
                            "routes": {"A4 (210 × 297 mm)": "Ruta automática A4"},
                            "sumatra": True,
                            "defaultPrinter": "Predeterminada de Windows",
                        }
                    }
                )
            elif request["method"] == "print":
                sent.append(request["params"])
                route.fulfill(
                    json={
                        "error": "Diagnóstico simulado: código 1. No se imprimió ningún documento."
                    }
                )
            else:
                route.continue_()

        page.route("**/api/engine", intercept)
        page.goto("http://127.0.0.1:1420")
        with page.expect_file_chooser() as chooser:
            page.get_by_role("button", name="Abrir documentos", exact=True).click()
        chooser.value.set_files(source)
        page.get_by_text("S/ 0.20", exact=True).wait_for(timeout=30000)
        page.get_by_label("Impresora", exact=True).select_option(
            "HP elegida por usuario"
        )
        page.locator("select").filter(
            has=page.locator('option[value="duplex"]')
        ).select_option("duplex")
        page.get_by_text("S/ 0.10", exact=True).wait_for(timeout=30000)
        page.get_by_role("button", name="Imprimir documento", exact=True).click()
        page.get_by_role("alert").wait_for()
        assert len(sent) == 1, sent
        assert sent[0]["printer"] == "HP elegida por usuario", sent
        assert sent[0]["settings"]["paper"] == "A4 (210 × 297 mm)", sent
        assert sent[0]["settings"]["duplex"] is True, sent
        assert "código 1" in page.get_by_role("alert").inner_text()
        assert (
            page.get_by_label("Impresora", exact=True).input_value()
            == "HP elegida por usuario"
        )
        browser.close()
    print(
        "Solicitud A4 dúplex verificada: conserva la impresora elegida, muestra el error y no reintenta. Sin impresión real."
    )


if __name__ == "__main__":
    main()
