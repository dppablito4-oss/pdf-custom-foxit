"""Check persisted appearance, contrast, document colors and compact layouts."""

import tempfile
from pathlib import Path

from playwright.sync_api import sync_playwright

from tests.test_core import sample_pdf


def main():
    screenshots = Path("artifacts/screenshots")
    screenshots.mkdir(parents=True, exist_ok=True)
    with (
        tempfile.TemporaryDirectory(prefix="grafiplot_theme_") as folder,
        sync_playwright() as pw,
    ):
        source = sample_pdf(Path(folder) / "Proyecto de impresión.pdf")
        browser = pw.chromium.launch(headless=True)
        page = browser.new_page(
            viewport={"width": 1440, "height": 1000}, reduced_motion="reduce"
        )
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto("http://127.0.0.1:1420")
        page.get_by_role("button", name="Modo oscuro", exact=True).wait_for()
        assert page.locator("html").get_attribute("data-theme") == "dark"
        assert (
            page.get_by_role("button", name="Modo oscuro", exact=True).get_attribute(
                "aria-pressed"
            )
            == "true"
        )
        with page.expect_file_chooser() as chooser:
            page.get_by_role("button", name="Abrir documentos", exact=True).click()
        chooser.value.set_files(source)
        page.get_by_role("img", name="Vista original, página 1").wait_for()
        page.get_by_text("S/ 0.50", exact=True).wait_for(timeout=30000)
        original_image = page.locator(".document-preview").get_attribute("src")
        for theme, label in [("dark", "Modo oscuro"), ("light", "Modo claro")]:
            page.get_by_role("button", name=label, exact=True).click()
            assert page.locator("html").get_attribute("data-theme") == theme
            assert (
                page.evaluate('localStorage.getItem("grafiplot.studio.theme")') == theme
            )
            assert (
                page.locator(".document-preview").get_attribute("src") == original_image
            )
            assert (
                page.locator(".paper-wrap").evaluate(
                    "el => getComputedStyle(el).backgroundColor"
                )
                == "rgb(255, 255, 255)"
            )
            # Contrast for controls and labels against their actual opaque parent background.
            contrast = page.evaluate("""() => {
              function rgb(value) { return value.match(/[\\d.]+/g).map(Number); }
              function luminance(color) { const values=rgb(color).slice(0,3).map(n=>{n/=255;return n<=.04045?n/12.92:((n+.055)/1.055)**2.4;});return values[0]*.2126+values[1]*.7152+values[2]*.0722; }
              return ['.field > span','.field select','.mode-field select','.estimate small','.printer-heading h2','.editor-tabs button.active','.button.primary'].map(selector=>{
                const element=document.querySelector(selector);let parent=element,backgrounds=[];
                while(parent){const style=getComputedStyle(parent);const stops=style.backgroundImage.match(/rgb\([^)]*\)/g);if(stops?.length){backgrounds=stops;break;}const values=rgb(style.backgroundColor);if(values.length===3||values[3]===1){backgrounds=[style.backgroundColor];break;}parent=parent.parentElement;}
                const a=luminance(getComputedStyle(element).color);
                return {selector,ratio:Math.min(...backgrounds.map(background=>{const b=luminance(background);return (Math.max(a,b)+.05)/(Math.min(a,b)+.05);}))};
              });
            }""")
            assert all(item["ratio"] >= 4.5 for item in contrast), contrast
            assert (
                page.locator(".field select").first.evaluate(
                    "el => parseFloat(getComputedStyle(el).fontSize)"
                )
                >= 14
            )
            assert (
                page.locator(".printer-heading h2").evaluate(
                    "el => parseInt(getComputedStyle(el).fontWeight)"
                )
                >= 700
            )
            page.screenshot(path=str(screenshots / f"estudio-{theme}.png"))
            page.get_by_role("button", name="Preferencias", exact=True).click()
            page.get_by_role(
                "heading", name="Preferencias de impresión", exact=True
            ).wait_for()
            page.screenshot(path=str(screenshots / f"preferencias-{theme}.png"))
            page.get_by_role("button", name="Guía rápida").click()
            page.get_by_role("dialog").wait_for()
            page.screenshot(path=str(screenshots / f"guia-{theme}.png"))
            page.get_by_role("button", name="Cerrar guía").click()
            page.get_by_role("button", name="Documentos", exact=True).click()
            page.set_viewport_size({"width": 1060, "height": 740})
            assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
            for button in ["Modo claro", "Modo oscuro", "Imprimir documento"]:
                bounds = page.get_by_role(
                    "button", name=button, exact=True
                ).bounding_box()
                assert (
                    bounds
                    and bounds["x"] >= 0
                    and bounds["x"] + bounds["width"] <= 1060
                    and bounds["y"] >= 0
                    and bounds["y"] + bounds["height"] <= 740
                ), (button, bounds)
            page.screenshot(path=str(screenshots / f"compacto-{theme}.png"))
            page.set_viewport_size({"width": 1440, "height": 1000})
        page.reload()
        page.get_by_role("button", name="Modo claro", exact=True).wait_for()
        assert page.locator("html").get_attribute("data-theme") == "light"
        assert (
            page.get_by_role("button", name="Modo claro", exact=True).get_attribute(
                "aria-pressed"
            )
            == "true"
        )
        page.get_by_role("button", name="Modo oscuro", exact=True).click()
        page.reload()
        page.get_by_role("button", name="Modo oscuro", exact=True).wait_for()
        assert page.locator("html").get_attribute("data-theme") == "dark"
        assert not errors, errors
        browser.close()
    print(
        "Apariencia OK: claro/oscuro persistentes, contraste >= 4.5:1, tipografía y ventana compacta."
    )


if __name__ == "__main__":
    main()
