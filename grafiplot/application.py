"""Application composition and shared Tk state initialization."""

import json
import tempfile
import tkinter as tk
from collections import OrderedDict
from pathlib import Path

from grafiplot.features.crop import CropMixin
from grafiplot.features.documents import DocumentsMixin
from grafiplot.features.groups import GroupsMixin
from grafiplot.features.merge import MergeMixin
from grafiplot.features.pages import PagesMixin
from grafiplot.features.preview import PreviewMixin
from grafiplot.features.printing import PrintingMixin
from grafiplot.features.reports import ReportsMixin
from grafiplot.ui.layout import LayoutMixin
from grafiplot.ui.settings import SettingsMixin
from grafiplot.ui.theme import ThemeMixin


class App(
    DocumentsMixin,
    PagesMixin,
    PreviewMixin,
    PrintingMixin,
    ReportsMixin,
    GroupsMixin,
    MergeMixin,
    CropMixin,
    SettingsMixin,
    LayoutMixin,
    ThemeMixin,
    tk.Tk,
):
    def __init__(self):
        super().__init__()
        self.title("GRAFIPLOT PDF PRINT — Estudio de impresión")
        width = min(1280, max(1024, self.winfo_screenwidth() - 80))
        height = min(840, max(640, self.winfo_screenheight() - 100))
        self.geometry(f"{width}x{height}")
        self.minsize(1024, 640)
        try:
            self.iconbitmap(
                str(Path(__file__).resolve().parent.parent / "GRAFIPLOT.ico")
            )
        except Exception:
            pass
        self.configure(bg="#0b0b0e")
        self.tmp = tempfile.TemporaryDirectory(prefix="grafiplot_")
        self.document = None
        self.source = None
        self.last_output = None
        self.photo = None
        self.thumbnails = []
        self.zoom = 1.0
        self.selected_pages = set()
        self.sent_pages = set()
        self.last_export_pages = set()
        self.anchor_page = None
        self.thumbnail_buttons = {}
        self.path = tk.StringVar(value="Ningún archivo seleccionado")
        self.mode = tk.StringVar(value="Normal")
        self.grid_type = tk.StringVar(value="4 hojas (2 × 2)")
        self.paper = tk.StringVar(value="A4 (210 × 297 mm)")
        self.orientation = tk.StringVar(value="Vertical")
        self.margin = tk.StringVar(value="5")
        self.overlap = tk.StringVar(value="5")
        self.cols = tk.StringVar(value="2")
        self.rows = tk.StringVar(value="2")
        self.cw = tk.StringVar(value="210")
        self.ch = tk.StringVar(value="297")
        self.excluded_pages = tk.StringVar(value="")
        self.page = tk.StringVar(value="Todas")
        self.print_order = tk.StringVar(value="")
        self.scale = tk.StringVar(value="Ajustar")
        self.per_sheet = tk.StringVar(value="1")
        self.nup_layout = tk.StringVar(value="Automática")
        self.nup_cols = tk.StringVar(value="2")
        self.nup_rows = tk.StringVar(value="2")
        self.nup_width = tk.StringVar(value="50")
        self.nup_height = tk.StringVar(value="70")
        self.nup_center = tk.BooleanVar(value=True)
        self.copies = tk.StringVar(value="1")
        self.printer = tk.StringVar(value="Impresora predeterminada")
        self.client = tk.StringVar(value="")
        self.content_pct = tk.StringVar(value="100")
        self.autorotate = tk.BooleanVar(value=True)
        self.group_name = tk.StringVar(value="")
        self.groups = {}
        self._skip_save_tab = None
        self.poster_whole = tk.BooleanVar(value=True)
        self.report_printer = tk.StringVar(value="Impresora predeterminada")
        self.config_path = Path.home() / "grafiplot_pdf_print_ajustes.json"
        try:
            self.routes = json.loads(self.config_path.read_text(encoding="utf-8"))
            if not isinstance(self.routes, dict):
                self.routes = {}
        except (OSError, ValueError):
            self.routes = {}
        self.report_printer.set(
            self.routes.get("_report_printer", "Impresora predeterminada")
        )
        self.thumb_size = tk.IntVar(value=90)
        self.preview_page = tk.IntVar(value=1)
        self.source_preview_page = 0
        self.duplex = tk.BooleanVar(value=False)
        self.book_price = tk.BooleanVar(value=True)
        self.tabs_data = {}
        self.active_tab = None
        self.switching_tabs = False
        self.job_log = []
        self._tab_images = {}
        self.crops = {}
        self.free_crops = {}
        self._free_points = []
        self._free_mode = False
        self._view_image_box = None
        self._crop_anchor = None
        self._crop_rectangle = None
        self._preview_timer = None
        self.temp_paths = []
        # Caché LRU en memoria; no convierte el PDF de impresión en imagen.
        self._preview_cache = OrderedDict()
        self._preview_cache_bytes = 0
        self._preview_cache_limit = 256 * 1024 * 1024
        self._thumb_generation = 0
        self._thumb_after = None
        self._thumb_images = {}
        self._resize_timer = None
        self._thumbnail_timer = None
        self._thumb_cache = OrderedDict()
        self._thumb_cache_limit = 300
        self.prepared_preview = None
        self.preview_doc = None
        self.preview_signature = None
        self.paper.trace_add("write", lambda *a: self.auto_printer())
        self.copies.trace_add("write", lambda *a: self.refresh_price())
        self._style()
        self._ui()
        self.refresh_printers()
        self.after(250, self.preview)
        self.protocol("WM_DELETE_WINDOW", self.close)
