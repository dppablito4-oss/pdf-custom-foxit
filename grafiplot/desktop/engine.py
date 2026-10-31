"""Document sessions and validated commands for the React desktop."""

import tempfile
import uuid
from pathlib import Path

from grafiplot.desktop.documents import DocumentsMixin
from grafiplot.desktop.output import OutputMixin
from grafiplot.desktop.printer_support import default_log_directory
from grafiplot.desktop.printing import PrintingMixin


class Engine(DocumentsMixin, OutputMixin, PrintingMixin):
    def __init__(self):
        self.workspace = tempfile.TemporaryDirectory(prefix="grafiplot_studio_")
        self.documents = {}
        self.previews = {}
        self.jobs = []
        self.config_path = Path.home() / "grafiplot_pdf_print_ajustes.json"
        self.log_directory = default_log_directory()

    def close(self):
        for document in self.documents.values():
            document["pdf"].close()
        self.documents.clear()
        self.workspace.cleanup()

    def call(self, method, params=None):
        actions = {
            "info": self.info,
            "open": self.open,
            "upload": self.upload,
            "close": self.close_document,
            "render": self.render,
            "prepare": self.prepare,
            "export": self.export,
            "edit": self.edit,
            "merge": self.merge,
            "print": self.print_document,
            "report": self.report,
            "save_routes": self.save_routes,
            "printer_dialog": self.printer_dialog,
        }
        if method not in actions:
            raise ValueError("Operación desconocida: " + str(method))
        return actions[method](**(params or {}))

    def _path(self, suffix=".pdf"):
        return str(Path(self.workspace.name) / (uuid.uuid4().hex + suffix))

    def _document(self, document_id):
        if document_id not in self.documents:
            raise ValueError("El documento ya no está abierto.")
        return self.documents[document_id]
