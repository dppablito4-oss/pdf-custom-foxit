"""Document sessions and validated commands for the React desktop."""

import base64
import tempfile
import uuid
from pathlib import Path

import pymupdf as fitz

from grafiplot.constants import ARCHIVES
from grafiplot.core.archives import unpack_archive
from grafiplot.core.conversion import make_pdf
from grafiplot.core.merge import combine_documents
from grafiplot.core.selection import selected_pdf


class DocumentsMixin:
    def _metadata(self, document_id):
        item = self._document(document_id)
        pdf = item["pdf"]
        return {
            "id": document_id,
            "name": item["name"],
            "pages": len(pdf),
            "size": Path(item["source"]).stat().st_size,
            "width": round(pdf[0].rect.width * 25.4 / 72, 1),
            "height": round(pdf[0].rect.height * 25.4 / 72, 1),
            "revision": item["revision"],
        }

    def _register(self, path, name=None, original=None):
        pdf = fitz.open(path)
        if pdf.needs_pass or not len(pdf):
            pdf.close()
            raise ValueError("El PDF está protegido o no contiene páginas.")
        document_id = uuid.uuid4().hex
        self.documents[document_id] = {
            "pdf": pdf,
            "source": str(path),
            "name": name or Path(path).name,
            "original": str(original or path),
            "revision": 0,
            "crops": {},
        }
        return self._metadata(document_id)

    def open(self, paths):
        opened, errors = [], []
        for path in paths:
            try:
                path = str(Path(path).resolve(strict=True))
                directory = tempfile.mkdtemp(dir=self.workspace.name)
                sources = (
                    unpack_archive(path, directory)
                    if Path(path).suffix.lower() in ARCHIVES
                    else [path]
                )
                for source in sources:
                    cache = tempfile.mkdtemp(dir=self.workspace.name)
                    converted = make_pdf(source, cache)
                    opened.append(self._register(converted, Path(source).name, source))
            except Exception as error:
                errors.append(f"{Path(path).name}: {error}")
        return {"documents": opened, "errors": errors}

    def upload(self, files):
        paths = []
        for file in files:
            name = Path(file["name"]).name
            folder = Path(tempfile.mkdtemp(dir=self.workspace.name))
            path = folder / name
            path.write_bytes(base64.b64decode(file["data"], validate=True))
            paths.append(str(path))
        return self.open(paths)

    def close_document(self, document_id):
        item = self._document(document_id)
        item["pdf"].close()
        del self.documents[document_id]
        self.previews.pop(document_id, None)
        return True

    def edit(self, document_id, action, pages=None, degrees=90, crop=None):
        item = self._document(document_id)
        pdf = item["pdf"]
        indexes = sorted(set(int(n) for n in (pages or [])))
        if any(n < 0 or n >= len(pdf) for n in indexes):
            raise ValueError("Página fuera del documento.")
        if action == "clear_crop":
            item["crops"].clear()
        elif action == "crop":
            if (
                not crop
                or len(crop) != 4
                or not 0 <= crop[0] < crop[2] <= 1
                or not 0 <= crop[1] < crop[3] <= 1
            ):
                raise ValueError("Seleccione un rectángulo de recorte válido.")
            for n in indexes or range(len(pdf)):
                rect = fitz.Rect(item["crops"].get(n, pdf[n].rect))
                item["crops"][n] = (
                    rect.x0 + crop[0] * rect.width,
                    rect.y0 + crop[1] * rect.height,
                    rect.x0 + crop[2] * rect.width,
                    rect.y0 + crop[3] * rect.height,
                )
        elif action in ("rotate", "delete"):
            if not indexes:
                raise ValueError("Seleccione al menos una página.")
            if action == "delete" and len(indexes) == len(pdf):
                raise ValueError("El documento debe conservar al menos una página.")
            with fitz.open() as edited:
                keep = [
                    n for n in range(len(pdf)) if action != "delete" or n not in indexes
                ]
                for n in keep:
                    edited.insert_pdf(pdf, from_page=n, to_page=n)
                    if action == "rotate" and n in indexes:
                        edited[-1].set_rotation((pdf[n].rotation + int(degrees)) % 360)
                target = self._path()
                edited.save(target, garbage=3, deflate=True)
            pdf.close()
            item["pdf"] = fitz.open(target)
            item["source"] = target
            item["crops"] = {
                new: item["crops"][old]
                for new, old in enumerate(keep)
                if old in item["crops"] and action != "rotate"
            }
        else:
            raise ValueError("Edición desconocida.")
        item["revision"] += 1
        self.previews.pop(document_id, None)
        return self._metadata(document_id)

    def merge(
        self,
        document_ids,
        exclusions=None,
        duplex=False,
        separator=False,
        pad_odd=False,
        rotate=False,
    ):
        sources = []
        # Materialize crops and edits in the merge, preserving the original documents.
        for document_id in document_ids:
            item = self._document(document_id)
            path = self._path()
            selected_pdf(
                item["pdf"], list(range(len(item["pdf"]))), path, item["crops"]
            )
            sources.append(path)
        output = self._path()
        try:
            combine_documents(
                sources,
                output,
                work_dir=self.workspace.name,
                exclusions=exclusions,
                duplex_mode=duplex,
                simplex_separator=separator,
                pad_each_odd=pad_odd,
                rotate_odd_landscape=rotate,
            )
            return self._register(output, "Combinado.pdf")
        finally:
            for path in sources:
                Path(path).unlink(missing_ok=True)
