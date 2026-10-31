"""Archive extraction with document and size limits."""

import shutil
import subprocess
import zipfile
from pathlib import Path

from grafiplot.constants import MAX_ARCHIVE_BYTES, MAX_ARCHIVE_FILES, SUPPORTED_MERGE


def unpack_archive(archive, destination):
    """Extract supported documents into isolated workspace. Never alter originals."""
    archive = Path(archive)
    root = Path(destination).resolve()
    root.mkdir(parents=True, exist_ok=True)
    if archive.suffix.lower() == ".zip":
        with zipfile.ZipFile(archive) as z:
            entries = [m for m in z.infolist() if not m.is_dir()]
            if (
                len(entries) > MAX_ARCHIVE_FILES
                or sum(m.file_size for m in entries) > MAX_ARCHIVE_BYTES
            ):
                raise ValueError(
                    "Archivo comprimido demasiado grande (máximo 500 archivos / 1 GB)."
                )
            paths = []
            for entry in entries:
                # Zip slip and Windows special paths guard. Unsupported formats are ignored.
                raw = entry.filename.replace("\\", "/")
                path = Path(raw)
                if (
                    path.is_absolute()
                    or ".." in path.parts
                    or ":" in raw
                    or not path.suffix.lower() in SUPPORTED_MERGE
                ):
                    continue
                target = (root / path).resolve()
                if not target.is_relative_to(root):
                    continue
                target.parent.mkdir(parents=True, exist_ok=True)
                with z.open(entry) as src, open(target, "wb") as dst:
                    shutil.copyfileobj(src, dst)
                paths.append(str(target))
            return paths
    if archive.suffix.lower() == ".rar":
        # RAR requires a compatible system extractor. 7z is supported by WinRAR / 7-Zip installers.
        candidates = [
            shutil.which("7z"),
            shutil.which("7za"),
            shutil.which("7zz"),
            r"C:\Program Files\7-Zip\7z.exe",
            r"C:\Program Files (x86)\7-Zip\7z.exe",
            r"C:\Program Files\WinRAR\UnRAR.exe",
            r"C:\Program Files\WinRAR\WinRAR.exe",
        ]
        exe = next((v for v in candidates if v and Path(v).is_file()), None)
        if not exe:
            raise RuntimeError(
                "Para extraer archivos RAR instale 7-Zip o WinRAR. Recomendado: 7-Zip."
            )
        # First list with 7zip where available; sandbox extraction and validate afterward.
        if Path(exe).name.lower().startswith(("7z", "7za")):
            command = [exe, "x", "-y", "-aoa", f"-o{root}", str(archive)]
        elif Path(exe).name.lower() == "unrar.exe":
            command = [exe, "x", "-o+", "-y", str(archive), str(root) + "\\"]
        else:
            command = [exe, "x", "-ibck", "-y", str(archive), str(root) + "\\"]
        completed = subprocess.run(command, capture_output=True, text=True, timeout=180)
        if completed.returncode:
            raise RuntimeError(
                "No se pudo descomprimir RAR: "
                + (completed.stderr or completed.stdout)[-350:]
            )
        paths = []
        size = 0
        for f in root.rglob("*"):
            if f.is_symlink():
                f.unlink()
                continue
            if not f.is_file():
                continue
            if not f.resolve().is_relative_to(root):
                continue
            size += f.stat().st_size
            if size > MAX_ARCHIVE_BYTES:
                raise ValueError("RAR supera el límite de 1 GB extraído.")
            if f.suffix.lower() in SUPPORTED_MERGE:
                paths.append(str(f))
            if len(paths) > MAX_ARCHIVE_FILES:
                raise ValueError("RAR supera 500 documentos.")
        return sorted(paths)
    raise ValueError("Tipo de archivo comprimido no compatible.")
