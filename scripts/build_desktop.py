"""Build the signed-off desktop distribution; no batch launcher is needed."""

import argparse
import json
import os
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main():
    parser = argparse.ArgumentParser(
        description="Compilar el escritorio y preparar la distribución."
    )
    parser.add_argument(
        "--reuse-engine",
        action="store_true",
        help="Reutilizar el motor PDF empaquetado para cambios exclusivos del frontend.",
    )
    parser.add_argument(
        "--package-only",
        action="store_true",
        help="Empaquetar una compilación ya generada de la versión actual.",
    )
    args = parser.parse_args()
    os.environ["PATH"] = (
        str(Path.home() / ".cargo" / "bin") + os.pathsep + os.environ["PATH"]
    )
    npm = shutil.which("npm.cmd")
    if not npm and not args.package_only:
        raise SystemExit("Se necesita Node.js con npm para compilar.")
    if args.package_only:
        pass
    elif args.reuse_engine:
        sidecar = (
            ROOT
            / "src-tauri"
            / "binaries"
            / "grafiplot-engine-x86_64-pc-windows-msvc.exe"
        )
        if not sidecar.is_file():
            raise SystemExit(
                "No hay motor empaquetado. Compile primero sin --reuse-engine."
            )
        subprocess.run([npm, "run", "tauri", "build"], cwd=ROOT, check=True)
    else:
        subprocess.run([npm, "run", "desktop:build"], cwd=ROOT, check=True)
    release = ROOT / "src-tauri" / "target" / "release"
    version = json.loads(
        (ROOT / "src-tauri" / "tauri.conf.json").read_text(encoding="utf-8")
    )["version"]
    if os.name == "nt":
        import win32api

        metadata = win32api.GetFileVersionInfo(
            str(release / "grafiplot-studio.exe"), "\\"
        )
        actual = f"{metadata['FileVersionMS']>>16}.{metadata['FileVersionMS']&65535}.{metadata['FileVersionLS']>>16}"
        if actual != version:
            raise SystemExit(
                f"La compilación es {actual}, pero el proyecto es {version}. Compile antes de empaquetar."
            )
    artifacts = ROOT / "artifacts"
    portable = artifacts / f"GRAFIPLOT Studio {version}"
    portable.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(release / "grafiplot-studio.exe", portable / "GRAFIPLOT Studio.exe")
    shutil.copyfile(release / "grafiplot-engine.exe", portable / "grafiplot-engine.exe")
    for installer in (release / "bundle" / "nsis").glob(f"*_{version}_*-setup.exe"):
        shutil.copyfile(installer, artifacts / installer.name)
    shutil.make_archive(
        str(artifacts / f"GRAFIPLOT-Studio-{version}-portable"), "zip", portable
    )
    print(f"Distribución lista en {artifacts}")


if __name__ == "__main__":
    main()
