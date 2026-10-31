"""Package Python/PyMuPDF into the Tauri sidecar, independent of system Python."""

import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main():
    cargo = Path.home() / ".cargo" / "bin"
    os.environ["PATH"] = str(cargo) + os.pathsep + os.environ["PATH"]
    rustc = shutil.which("rustc")
    if not rustc:
        raise SystemExit(
            "Falta Rust. Instale rustup con el destino x86_64-pc-windows-msvc."
        )
    version = subprocess.check_output([rustc, "-vV"], text=True)
    target = next(
        line.split(": ", 1)[1]
        for line in version.splitlines()
        if line.startswith("host:")
    )
    output = ROOT / "src-tauri" / "binaries"
    output.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            sys.executable,
            "-m",
            "PyInstaller",
            "--noconfirm",
            "--clean",
            "--onefile",
            "--console",
            "--name",
            "grafiplot-engine",
            "--distpath",
            str(ROOT / ".build" / "engine"),
            "--workpath",
            str(ROOT / ".build" / "pyinstaller"),
            "--specpath",
            str(ROOT / ".build"),
            "--paths",
            str(ROOT),
            "--collect-all",
            "pymupdf",
            "--hidden-import",
            "win32print",
            "--exclude-module",
            "tkinter",
            str(ROOT / "scripts" / "engine_entry.py"),
        ],
        cwd=ROOT,
        check=True,
    )
    shutil.copyfile(
        ROOT / ".build" / "engine" / "grafiplot-engine.exe",
        output / f"grafiplot-engine-{target}.exe",
    )
    print("Motor PDF empaquetado: " + str(output))


if __name__ == "__main__":
    main()
