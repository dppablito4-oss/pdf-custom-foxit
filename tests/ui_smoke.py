"""Run with `python -m tests.ui_smoke`; uses Tk but never sends anything to a printer."""

import hashlib
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pymupdf as fitz

from grafiplot.application import App
from tests.test_core import sample_pdf


class DesktopTests(unittest.TestCase):
    def setUp(self):
        self.workspace = tempfile.TemporaryDirectory(prefix="grafiplot_ui_")
        self.addCleanup(self.workspace.cleanup)
        self.root = Path(self.workspace.name)
        self.first = sample_pdf(self.root / "first.pdf")
        self.second = sample_pdf(self.root / "second.pdf", 2)
        self.original = hashlib.sha256(Path(self.first).read_bytes()).digest()
        self.errors = []
        self.app = App()
        self.app.withdraw()
        self.app.report_callback_exception = lambda *error: self.errors.append(error)
        self.addCleanup(self.app.close)
        self.patches = []
        for name in ("showerror", "showwarning", "showinfo"):
            mock = self.enterContext(patch("tkinter.messagebox." + name))
            self.patches.append(mock)
        self.app.update()

    def tearDown(self):
        self.assertEqual(self.errors, [], "Tk callbacks raised exceptions")
        for mock in self.patches:
            mock.assert_not_called()
        self.assertEqual(
            hashlib.sha256(Path(self.first).read_bytes()).digest(), self.original
        )

    def open(self):
        self.app.open_paths([self.first])
        self.app.update()

    def test_open_preview_all_modes_and_close_last_document(self):
        self.open()
        for mode, expected in [
            ("Normal", 5),
            ("Póster", 20),
            ("Folleto", 4),
            ("Varias páginas por hoja", 5),
        ]:
            with self.subTest(mode=mode):
                self.app.mode.set(mode)
                self.app.prepare_preview(silent=True)
                self.assertIsNotNone(self.app.preview_doc)
                self.assertEqual(len(self.app.preview_doc), expected)
        self.app.close_tab()
        self.app.update()
        self.assertIsNone(self.app.document)
        self.assertFalse(self.app.selected_pages)
        self.assertFalse(self.app.tab_buttons)
        self.assertTrue(
            all("disabled" in button.state() for button in self.app.document_actions)
        )

    def test_nup_settings_survive_tab_changes_and_new_tabs_reset(self):
        self.open()
        first_tab = self.app.active_tab
        self.app.mode.set("Varias páginas por hoja")
        self.app.nup_layout.set("A medida (mm, separación 5 mm)")
        self.app.nup_width.set("60")
        self.app.nup_height.set("85")
        self.app.nup_cols.set("3")
        self.app.nup_rows.set("4")
        self.app.nup_center.set(False)
        self.app.open_paths([self.second])
        self.app.update()
        self.assertEqual(self.app.mode.get(), "Normal")
        self.assertEqual(self.app.nup_layout.get(), "Automática")
        self.assertEqual(self.app.nup_width.get(), "50")
        self.app.tabs.select(first_tab)
        self.app.on_tab_changed()
        self.app.update()
        self.assertEqual(self.app.mode.get(), "Varias páginas por hoja")
        self.assertEqual(self.app.nup_layout.get(), "A medida (mm, separación 5 mm)")
        self.assertEqual(self.app.nup_width.get(), "60")
        self.assertEqual(self.app.nup_height.get(), "85")
        self.assertEqual(self.app.nup_cols.get(), "3")
        self.assertEqual(self.app.nup_rows.get(), "4")
        self.assertFalse(self.app.nup_center.get())

    def test_selection_order_rotation_and_report_preserve_source(self):
        self.open()
        self.app.print_order.set("3,1,1")
        subset, _, pages = self.app.selected_source()
        with fitz.open(subset) as document:
            self.assertEqual(
                [page.get_text().strip() for page in document],
                ["PAGE 3", "PAGE 1", "PAGE 1"],
            )
        self.assertEqual(pages, {0, 2})
        self.app.select_thumbnail(0)
        self.app.rotate_selected_pages(90)
        self.assertEqual(self.app.document[0].rotation, 90)
        report = self.root / "report.pdf"
        self.app.build_report_pdf(str(report))
        with fitz.open(report) as document:
            self.assertIn("REPORTE", document[0].get_text())

    def test_custom_paper_and_mode_controls(self):
        self.open()
        self.app.paper.set("Personalizado")
        self.assertTrue(self.app.custom_dims.winfo_manager())
        self.app.mode.set("Folleto")
        self.assertTrue(self.app.duplex.get())
        self.assertIn("disabled", self.app.duplex_control.state())
        self.app.mode.set("Póster")
        self.assertTrue(self.app.poster_options.winfo_manager())
        self.assertFalse(self.app.nup_options.winfo_manager())
        self.app.mode.set("Normal")
        self.assertFalse(self.app.poster_options.winfo_manager())

    def test_small_and_large_window_keep_main_controls_in_bounds(self):
        self.app.deiconify()
        for width, height in [(1024, 640), (1280, 840)]:
            with self.subTest(width=width):
                self.app.geometry(f"{width}x{height}")
                self.app.update()
                self.assertGreaterEqual(self.app.canvas.winfo_width(), 350)
                self.assertGreaterEqual(self.app.canvas.winfo_height(), 160)
                for widget in self.app.document_actions + [
                    self.app.top_printer_combo,
                    self.app.duplex_control,
                ]:
                    self.assertTrue(widget.winfo_viewable())
                    right = (
                        widget.winfo_rootx()
                        - self.app.winfo_rootx()
                        + widget.winfo_width()
                    )
                    self.assertLessEqual(right, self.app.winfo_width())

    def test_incomplete_numeric_input_does_not_break_tab_switching(self):
        self.open()
        self.app.copies.set("")
        self.app.content_pct.set("")
        self.app.open_paths([self.second])
        self.app.update()
        self.assertEqual(self.app.path.get(), "second.pdf")


if __name__ == "__main__":
    unittest.main(verbosity=2)
