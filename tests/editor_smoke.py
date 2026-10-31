"""Editor UI interactions with real PDFs; printing and driver dialogs are intercepted."""

import tempfile
from pathlib import Path

from playwright.sync_api import sync_playwright

from tests.test_core import sample_pdf


def main():
    screenshots = Path("artifacts/screenshots")
    screenshots.mkdir(parents=True, exist_ok=True)
    with (
        tempfile.TemporaryDirectory(prefix="grafiplot_editor_") as folder,
        sync_playwright() as pw,
    ):
        source = sample_pdf(Path(folder) / "Documento de trabajo.pdf", 30)
        browser = pw.chromium.launch(headless=True)
        page = browser.new_page(
            viewport={"width": 1440, "height": 980}, reduced_motion="reduce"
        )
        errors = []
        dialogs = []
        edits = []
        page.on("pageerror", lambda error: errors.append(str(error)))

        def intercept(route):
            data = route.request.post_data_json
            if data["method"] == "printer_dialog":
                dialogs.append(data["params"])
                route.fulfill(json={"result": True})
            elif data["method"] == "print":
                raise AssertionError("This test must not print.")
            else:
                if data["method"] == "edit":
                    edits.append(data["params"])
                route.continue_()

        page.route("**/api/engine", intercept)
        page.goto("http://127.0.0.1:1420")
        page.get_by_text("Sin documento", exact=True).first.wait_for()
        assert (
            page.get_by_role("button", name="Abrir documentos", exact=True).count() == 1
        )
        assert page.locator(".empty-state,.sidebar,.topbar,.toast").count() == 0
        with page.expect_file_chooser() as chooser:
            page.get_by_role("button", name="Abrir documentos", exact=True).click()
        chooser.value.set_files(source)
        page.get_by_role("img", name="Vista original, página 1").wait_for(timeout=30000)
        page.get_by_text("S/ 3.00", exact=True).wait_for(timeout=30000)
        assert page.get_by_role("status").count() == 1
        page.screenshot(path=str(screenshots / "editor-oscuro.png"))
        # Drag the actual splitter; multiple thumbnail columns should become available.
        separator = page.get_by_role("separator", name="Ancho del panel de páginas")
        box = separator.bounding_box()
        assert box
        page.mouse.move(box["x"] + 3, box["y"] + 100)
        page.mouse.down()
        page.mouse.move(box["x"] + 220, box["y"] + 100, steps=15)
        page.mouse.up()
        width = page.locator(".page-rail").evaluate("el=>el.clientWidth")
        assert width > 400, width
        buttons = page.locator(".thumbnail")
        first = buttons.nth(0).bounding_box()
        second = buttons.nth(1).bounding_box()
        third = buttons.nth(2).bounding_box()
        assert first and second and third and first["y"] == second["y"]
        grid = page.locator(".thumbnails").bounding_box()
        assert grid
        # A blank-space marquee surrounds first-row thumbnails.
        page.mouse.move(grid["x"] + 3, grid["y"] + 3)
        page.mouse.down()
        page.mouse.move(
            second["x"] + second["width"] - 2,
            second["y"] + second["height"] - 2,
            steps=16,
        )
        page.wait_for_timeout(150)
        page.mouse.up()
        assert page.locator('.thumbnail[aria-pressed="true"]').count() == 2
        # Ctrl click, shift range, then Ctrl+A and Escape within the thumbnail panel.
        page.get_by_role("button", name="Página 4", exact=True).click(
            modifiers=["Control"]
        )
        assert page.locator('.thumbnail[aria-pressed="true"]').count() == 3
        page.get_by_role("button", name="Página 7", exact=True).click(
            modifiers=["Shift"]
        )
        assert page.locator('.thumbnail[aria-pressed="true"]').count() == 6
        page.get_by_role("button", name="Página 7", exact=True).press("Control+a")
        assert page.locator('.thumbnail[aria-pressed="true"]').count() == 30
        page.get_by_role("button", name="Página 7", exact=True).press("Escape")
        assert page.locator('.thumbnail[aria-pressed="true"]').count() == 0
        page.get_by_role("button", name="Página 1", exact=True).click()
        page.get_by_role("button", name="Página 1", exact=True).press("ArrowRight")
        assert (
            page.get_by_role("button", name="Página 2", exact=True).get_attribute(
                "aria-pressed"
            )
            == "true"
        )
        # Autoscroll a marquee while holding the pointer at the lower edge.
        page.locator(".thumbnails").evaluate("el=>el.scrollTop=0")
        grid = page.locator(".thumbnails").bounding_box()
        assert grid
        page.mouse.move(grid["x"] + 3, grid["y"] + 3)
        page.mouse.down()
        page.mouse.move(
            grid["x"] + grid["width"] - 8, grid["y"] + grid["height"] - 3, steps=12
        )
        page.wait_for_timeout(700)
        page.mouse.up()
        assert page.locator(".thumbnails").evaluate("el=>el.scrollTop") > 50
        page.screenshot(path=str(screenshots / "editor-seleccion.png"))
        page.get_by_role("button", name="Limpiar selección", exact=True).click()
        page.get_by_text("S/ 3.00", exact=True).wait_for(timeout=30000)
        # Use exact engine requests for the selected printer's two different native dialogs.
        printer = page.get_by_label("Impresora", exact=True).input_value()
        page.get_by_role("button", name="Preferencias del driver", exact=True).click()
        page.get_by_role("button", name="Propiedades", exact=True).click()
        assert dialogs == [
            {"printer": printer, "properties": False},
            {"printer": printer, "properties": True},
        ], dialogs
        # The top ribbon activates a real rectangular crop on the source image.
        page.get_by_role("button", name="Recortar con el mouse", exact=True).click()
        image = page.get_by_role("img", name="Vista original, página 2")
        bounds = image.bounding_box()
        assert bounds
        page.mouse.move(
            bounds["x"] + bounds["width"] * 0.1, bounds["y"] + bounds["height"] * 0.1
        )
        page.mouse.down()
        page.mouse.move(
            bounds["x"] + bounds["width"] * 0.65,
            bounds["y"] + bounds["height"] * 0.45,
            steps=12,
        )
        page.mouse.up()
        page.get_by_role("status").filter(has_text="Recorte aplicado").wait_for()
        assert edits[-1]["action"] == "crop" and len(edits[-1]["crop"]) == 4, edits
        assert (
            page.get_by_role(
                "button", name="Recortar con el mouse", exact=True
            ).get_attribute("aria-pressed")
            == "false"
        )
        page.get_by_role("button", name="Quitar recortes", exact=True).click()
        page.get_by_role("status").filter(has_text="Recortes eliminados").wait_for()
        assert edits[-1]["action"] == "clear_crop"
        # A compact window must keep the editor and printer actions reachable.
        page.set_viewport_size({"width": 1060, "height": 740})
        assert page.evaluate("document.documentElement.scrollWidth<=innerWidth")
        assert page.locator(".preview-canvas").evaluate("el=>el.clientWidth") >= 290
        for name in [
            "Abrir documentos",
            "Recortar con el mouse",
            "Preferencias del driver",
            "Imprimir documento",
        ]:
            b = page.get_by_role("button", name=name, exact=True).bounding_box()
            assert (
                b
                and b["x"] >= 0
                and b["x"] + b["width"] <= 1060
                and b["y"] + b["height"] <= 740
            ), (name, b)
        page.screenshot(path=str(screenshots / "editor-compacto.png"))
        page.get_by_role("button", name="Modo claro", exact=True).click()
        page.set_viewport_size({"width": 1440, "height": 980})
        page.screenshot(path=str(screenshots / "editor-claro.png"))
        assert not errors, errors
        browser.close()
    print(
        "Editor OK: panel redimensionable, selección rectangular, Ctrl/Shift, teclado, autoscroll y acceso a ambos diálogos de driver. Sin impresión real."
    )


if __name__ == "__main__":
    main()
