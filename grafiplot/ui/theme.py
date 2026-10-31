"""Shared palette and accessible ttk styles for the desktop workspace."""

from tkinter import ttk

COLORS = {
    "background": "#eef1f5",
    "surface": "#ffffff",
    "soft": "#f6f7fa",
    "border": "#dce1e8",
    "text": "#202735",
    "muted": "#667085",
    "accent": "#b51f38",
    "accent_hover": "#94182d",
    "canvas": "#e3e7ed",
}


class ThemeMixin:
    def _style(self):
        self.configure(background=COLORS["background"])
        self.option_add("*Font", ("Segoe UI", 10))
        self.option_add("*TCombobox*Listbox.font", ("Segoe UI", 10))
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure(".", font=("Segoe UI", 10))
        style.configure("TFrame", background=COLORS["background"])
        style.configure("Panel.TFrame", background=COLORS["surface"])
        style.configure("Soft.TFrame", background=COLORS["soft"])
        style.configure(
            "TLabel", background=COLORS["surface"], foreground=COLORS["text"]
        )
        style.configure(
            "Muted.TLabel", foreground=COLORS["muted"], font=("Segoe UI", 9)
        )
        style.configure(
            "Footer.TLabel",
            background=COLORS["background"],
            foreground=COLORS["muted"],
            font=("Segoe UI", 9),
        )
        style.configure(
            "Brand.TLabel", font=("Segoe UI", 20, "bold"), foreground=COLORS["accent"]
        )
        style.configure("Heading.TLabel", font=("Segoe UI", 12, "bold"))
        style.configure(
            "Section.TLabel", font=("Segoe UI", 9, "bold"), foreground=COLORS["muted"]
        )
        style.configure(
            "Price.TLabel", font=("Segoe UI", 10, "bold"), foreground=COLORS["accent"]
        )
        style.configure(
            "TButton",
            background=COLORS["soft"],
            foreground=COLORS["text"],
            padding=(11, 7),
            borderwidth=1,
            bordercolor=COLORS["border"],
            relief="flat",
        )
        style.map(
            "TButton",
            background=[
                ("disabled", "#f4f5f7"),
                ("pressed", "#dce1e8"),
                ("active", "#e8ebf0"),
            ],
            foreground=[("disabled", "#939baa")],
            bordercolor=[("focus", COLORS["accent"])],
        )
        style.configure(
            "Primary.TButton",
            background=COLORS["accent"],
            foreground="white",
            font=("Segoe UI", 10, "bold"),
            borderwidth=0,
        )
        style.map(
            "Primary.TButton",
            background=[("disabled", "#e5c8ce"), ("active", COLORS["accent_hover"])],
            foreground=[("disabled", "#ffffff"), ("active", "#ffffff")],
        )
        style.configure(
            "Dark.TButton",
            background=COLORS["text"],
            foreground="white",
            font=("Segoe UI", 10, "bold"),
            borderwidth=0,
        )
        style.map(
            "Dark.TButton",
            background=[("disabled", "#dce1e8"), ("active", "#394356")],
            foreground=[("disabled", "#939baa"), ("active", "#ffffff")],
        )
        style.configure("Compact.TButton", font=("Segoe UI", 9), padding=(8, 5))
        style.configure("Preview.TButton", padding=(10, 6))
        style.configure(
            "TEntry",
            padding=(6, 5),
            fieldbackground="white",
            foreground=COLORS["text"],
            bordercolor=COLORS["border"],
        )
        style.configure(
            "TCombobox",
            padding=(6, 5),
            fieldbackground="white",
            background=COLORS["soft"],
            foreground=COLORS["text"],
            bordercolor=COLORS["border"],
            arrowsize=12,
        )
        style.map(
            "TCombobox",
            fieldbackground=[("readonly", "white"), ("disabled", COLORS["soft"])],
            foreground=[("disabled", "#939baa"), ("readonly", COLORS["text"])],
        )
        style.configure(
            "TSpinbox",
            padding=(5, 4),
            fieldbackground="white",
            arrowsize=12,
            bordercolor=COLORS["border"],
        )
        style.configure(
            "TCheckbutton",
            background="white",
            foreground=COLORS["text"],
            padding=(0, 3),
        )
        style.map(
            "TCheckbutton",
            background=[("active", "white")],
            foreground=[("disabled", "#939baa")],
        )
        style.configure("TRadiobutton", background="white", foreground=COLORS["text"])
        style.configure(
            "TScrollbar",
            background="#d1d7e0",
            troughcolor=COLORS["soft"],
            borderwidth=0,
            arrowsize=12,
        )
        style.configure("TScale", background="white", troughcolor=COLORS["border"])
        style.configure("TSeparator", background=COLORS["border"])
        style.layout("GRAFI.Hidden.TNotebook.Tab", [])
        style.configure(
            "GRAFI.Hidden.TNotebook",
            tabmargins=0,
            borderwidth=0,
            background=COLORS["background"],
        )
