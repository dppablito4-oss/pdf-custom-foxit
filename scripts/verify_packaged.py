"""Smoke-test the built PDF executable, not the development Python interpreter."""

import json
import subprocess
import tempfile
from pathlib import Path

import pymupdf as fitz

ROOT = Path(__file__).resolve().parent.parent


def main():
    version = json.loads(
        (ROOT / "src-tauri" / "tauri.conf.json").read_text(encoding="utf-8")
    )["version"]
    executable = (
        ROOT / "artifacts" / f"GRAFIPLOT Studio {version}" / "grafiplot-engine.exe"
    )
    assert executable.is_file(), "Primero genere la distribución con build_desktop.py"
    with tempfile.TemporaryDirectory(prefix="grafiplot_packaged_test_") as folder:
        source = Path(folder) / "Verificación español.pdf"
        with fitz.open() as pdf:
            for number in range(3):
                page = pdf.new_page()
                page.insert_text((50, 70), f"PAGE {number+1}")
            pdf.save(source)
        process = subprocess.Popen(
            [str(executable)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            encoding="utf-8",
            creationflags=subprocess.CREATE_NO_WINDOW,
        )

        def request(method, params=None):
            process.stdin.write(
                json.dumps(
                    {"method": method, "params": params or {}}, ensure_ascii=False
                )
                + "\n"
            )
            process.stdin.flush()
            result = json.loads(process.stdout.readline())
            assert "error" not in result, result
            return result["result"]

        try:
            info = request("info")
            assert info["papers"]
            doc = request("open", {"paths": [str(source)]})["documents"][0]
            assert doc["pages"] == 3
            settings = {"mode": "booklet", "paper": "A4 (210 × 297 mm)", "copies": 1}
            result = request(
                "prepare", {"document_id": doc["id"], "settings": settings}
            )
            assert result["pages"] == 2 and result["sheets"] == 1
            image = request(
                "render", {"document_id": doc["id"], "preview": True, "width": 200}
            )
            assert image["image"].startswith("data:image/png;base64,")
            output = Path(folder) / "resultado.pdf"
            request(
                "export",
                {"document_id": doc["id"], "settings": settings, "path": str(output)},
            )
            with fitz.open(output) as pdf:
                assert len(pdf) == 2
            process.stdin.write('{"method":"shutdown"}\n')
            process.stdin.flush()
            process.wait(timeout=15)
            assert process.returncode == 0
        finally:
            if process.poll() is None:
                process.kill()
                process.wait()
    print(
        "Ejecutable PDF verificado: apertura Unicode, folleto, renderizado, exportación y cierre limpio."
    )


if __name__ == "__main__":
    main()
