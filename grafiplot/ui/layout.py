"""Compose the workspace and register shared events; panels live in separate files."""

from tkinter import ttk

from grafiplot.ui.header import build_document_strip, build_header
from grafiplot.ui.sidebar import build_sidebar
from grafiplot.ui.workspace import build_workspace


class LayoutMixin:
    def _ui(self):
        self.document_actions = []
        build_header(self)
        build_document_strip(self)
        footer = ttk.Frame(self)
        footer.pack(side="bottom", fill="x", padx=18, pady=(0, 9))
        self.footer_path = ttk.Label(
            footer, textvariable=self.path, style="Footer.TLabel", width=30
        )
        self.footer_path.pack(side="left", fill="x", expand=True)
        ttk.Label(
            footer,
            text="Ctrl+O  Abrir    ·    Ctrl+S  Guardar PDF    ·    Ctrl+Tab  Cambiar archivo",
            style="Footer.TLabel",
        ).pack(side="right")
        body = ttk.Frame(self)
        body.pack(fill="both", expand=True, padx=16, pady=(0, 10))
        build_sidebar(self, body)
        build_workspace(self, body)
        self.update_action_state()
        self._bind_events()

    def _bind_events(self):
        self.tabs.bind("<<NotebookTabChanged>>", self.on_tab_changed)
        for event, action in {
            "<Control-o>": self.open_file,
            "<Control-s>": self.export,
            "<Control-w>": self.close_tab,
        }.items():
            self.bind(event, lambda e, action=action: self._shortcut(action))
        self.bind("<Control-Tab>", lambda e: self.navigate_tabs(1))
        self.bind("<Control-Shift-Tab>", lambda e: self.navigate_tabs(-1))
        self.bind("<Delete>", self.delete_selected_pages)
        self.bind("<KP_Delete>", self.delete_selected_pages)
        self.bind_all("<MouseWheel>", self.settings_wheel, add="+")
        self.bind_all("<Button-4>", self.settings_wheel, add="+")
        self.bind_all("<Button-5>", self.settings_wheel, add="+")
        self.grid_type.trace_add(
            "write", lambda *a: (self.sync_grid(), self.update_mode_controls())
        )
        for variable in (self.mode, self.paper, self.nup_layout):
            variable.trace_add("write", lambda *a: self.update_mode_controls())
        for variable in (
            self.orientation,
            self.cols,
            self.rows,
            self.margin,
            self.overlap,
            self.page,
            self.cw,
            self.ch,
            self.scale,
            self.per_sheet,
            self.nup_cols,
            self.nup_rows,
            self.nup_width,
            self.nup_height,
            self.content_pct,
            self.autorotate,
            self.print_order,
        ):
            variable.trace_add("write", lambda *a: self.invalidate_preview())
        self.after_idle(self.update_mode_controls)

    @staticmethod
    def _shortcut(action):
        action()
        return "break"

    def update_action_state(self):
        """Make available actions clear, including after closing the last tab."""
        for button in getattr(self, "document_actions", ()):
            button.state(["!disabled"] if self.document else ["disabled"])

    def resize_preview(self, event=None):
        if self._resize_timer is not None:
            self.after_cancel(self._resize_timer)
        self._resize_timer = self.after(100, self._render_resized_preview)

    def _render_resized_preview(self):
        self._resize_timer = None
        self.preview()
