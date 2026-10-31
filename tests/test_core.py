"""Regression checks using real PDFs and images; never submits print jobs."""

import hashlib
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

import pymupdf as fitz
from PIL import Image

from grafiplot.core.archives import unpack_archive
from grafiplot.core.conversion import make_pdf
from grafiplot.core.layout import create_output, make_booklet, make_nup, points
from grafiplot.core.merge import combine_documents
from grafiplot.core.pages import parse_excluded_pages, parse_page_order
from grafiplot.core.printing import build_print_command
from grafiplot.core.selection import selected_pdf


def sample_pdf(path, pages=5):
    with fitz.open() as document:
        for number in range(1, pages + 1):
            page = document.new_page(width=300, height=420)
            page.insert_text((30, 40), f"PAGE {number}", fontsize=20)
        document.save(path)
    return str(path)


class PdfTests(unittest.TestCase):
    def setUp(self):
        self.workspace = tempfile.TemporaryDirectory(prefix="grafiplot_test_")
        self.addCleanup(self.workspace.cleanup)
        self.root = Path(self.workspace.name)
        self.source = sample_pdf(self.root / "source.pdf")
        self.original = hashlib.sha256(Path(self.source).read_bytes()).digest()

    def tearDown(self):
        self.assertEqual(
            hashlib.sha256(Path(self.source).read_bytes()).digest(), self.original
        )

    def output(self, mode="Normal", **options):
        path = self.root / "output.pdf"
        count = create_output(
            self.source,
            str(path),
            mode,
            2,
            2,
            (210, 297),
            False,
            5,
            5,
            page_number=-1,
            **options,
        )
        return path, count

    def test_normal_keeps_text_and_paper_dimensions(self):
        path, count = self.output()
        self.assertEqual(count, 5)
        with fitz.open(path) as document:
            self.assertAlmostEqual(document[0].rect.width, points(210), places=2)
            self.assertAlmostEqual(document[0].rect.height, points(297), places=2)
            self.assertEqual(
                [p.get_text().strip() for p in document],
                [f"PAGE {n}" for n in range(1, 6)],
            )

    def test_poster_creates_four_tiles_per_page(self):
        path, count = self.output("Póster")
        self.assertEqual(count, 20)
        with fitz.open(path) as document:
            self.assertTrue(any("PAGE 1" in document[n].get_text() for n in range(4)))

    def test_booklet_pads_and_imposes_front_then_back(self):
        path, count = self.output("Folleto")
        self.assertEqual(count, 4)
        with fitz.open(path) as document:
            self.assertGreater(document[0].rect.width, document[0].rect.height)
            for index, number in [(0, 1), (1, 2), (2, 3), (3, 5)]:
                self.assertIn(f"PAGE {number}", document[index].get_text())

    def test_automatic_nup_keeps_all_pages(self):
        path, count = self.output("Varias páginas por hoja", per_sheet=2)
        self.assertEqual(count, 3)
        with fitz.open(path) as document:
            self.assertIn("PAGE 1", document[0].get_text())
            self.assertIn("PAGE 2", document[0].get_text())
            self.assertIn("PAGE 5", document[2].get_text())

    def test_explicit_nup_grid(self):
        _, count = self.output("Varias páginas por hoja", per_sheet=1202)
        self.assertEqual(count, 2)

    def test_all_on_one_sheet(self):
        _, count = self.output("Varias páginas por hoja", per_sheet=("all",))
        self.assertEqual(count, 1)

    def test_measured_cells(self):
        _, count = self.output("Varias páginas por hoja", per_sheet=("measure", 50, 70))
        self.assertEqual(count, 1)

    def test_invalid_margins_release_pdf_handles(self):
        for function in (make_booklet, make_nup):
            with self.assertRaises(ValueError):
                function(
                    self.source, str(self.root / "bad.pdf"), (210, 297), False, 200
                )
            renamed = self.root / "renamed.pdf"
            Path(self.source).rename(renamed)
            renamed.rename(self.source)

    def test_merge_exclusions_and_duplex_padding(self):
        second = sample_pdf(self.root / "second.pdf", 3)
        result, count = combine_documents(
            [self.source, second],
            self.root / "merged.pdf",
            exclusions=["2-5", "2-3"],
            duplex_mode=True,
        )
        self.assertEqual(count, 6)
        with fitz.open(result) as document:
            self.assertEqual(
                [p.get_text().strip() for p in document],
                ["PAGE 1", "", "", "", "PAGE 1", ""],
            )

    def test_blank_separator_pages_survive_all_output_modes(self):
        blank = self.root / "blank.pdf"
        with fitz.open() as document:
            document.new_page()
            document.save(blank)
        for mode in ("Normal", "Póster", "Folleto", "Varias páginas por hoja"):
            with self.subTest(mode=mode):
                result = self.root / f"{mode}.pdf"
                count = create_output(
                    str(blank),
                    str(result),
                    mode,
                    2,
                    2,
                    (210, 297),
                    False,
                    5,
                    5,
                    page_number=-1,
                )
                self.assertGreater(count, 0)

    def test_merge_refuses_overwriting_original_or_existing_output(self):
        second = sample_pdf(self.root / "second.pdf", 1)
        with self.assertRaises(ValueError):
            combine_documents([self.source, second], self.source)
        existing = self.root / "exists.pdf"
        existing.write_bytes(b"preserve")
        with self.assertRaises(FileExistsError):
            combine_documents([self.source, second], existing)
        self.assertEqual(existing.read_bytes(), b"preserve")

    def test_multipage_tiff_conversion(self):
        source = self.root / "scan.tiff"
        frames = [Image.new("RGB", (100, 150), color) for color in ("red", "blue")]
        frames[0].save(source, save_all=True, append_images=frames[1:], dpi=(150, 150))
        original = source.read_bytes()
        result = make_pdf(str(source), self.workspace.name)
        with fitz.open(result) as document:
            self.assertEqual(len(document), 2)
        self.assertEqual(source.read_bytes(), original)

    def test_zip_skips_unsafe_and_unsupported_paths(self):
        archive = self.root / "batch.zip"
        with zipfile.ZipFile(archive, "w") as packed:
            packed.write(self.source, "documents/valid.pdf")
            for name in (
                "../escape.pdf",
                "C:/escape.pdf",
                "/absolute.pdf",
                "script.exe",
            ):
                packed.writestr(name, b"ignored")
        destination = self.root / "extracted"
        paths = unpack_archive(archive, destination)
        self.assertEqual(
            paths, [str((destination / "documents" / "valid.pdf").resolve())]
        )
        self.assertFalse((self.root / "escape.pdf").exists())

    def test_selected_pdf_preserves_order_and_cropped_vector_text(self):
        output = self.root / "selected.pdf"
        with fitz.open(self.source) as document:
            selected_pdf(document, [2, 0, 0], str(output), {0: (10, 10, 280, 200)})
        with fitz.open(output) as document:
            self.assertEqual(
                [page.get_text().strip() for page in document],
                ["PAGE 3", "PAGE 1", "PAGE 1"],
            )
            self.assertEqual(document[1].rect.width, 270)

    def test_invalid_selection_and_crop_are_rejected(self):
        with fitz.open(self.source) as document:
            for indexes, crops in [([], {}), ([0], {0: (900, 900, 950, 950)})]:
                with self.assertRaises(ValueError):
                    selected_pdf(
                        document, indexes, str(self.root / "invalid.pdf"), crops
                    )


class SelectionTests(unittest.TestCase):
    def test_exclusions_are_zero_based(self):
        self.assertEqual(parse_excluded_pages("1;3-5", 6), {0, 2, 3, 4})

    def test_order_retains_duplicates(self):
        self.assertEqual(parse_page_order("2,2;4-5,1", 6), [1, 1, 3, 4, 0])

    def test_invalid_and_extreme_ranges_are_rejected(self):
        for spec in ("0", "7", "3-1", "abc", "1-999999999999999"):
            with self.subTest(spec=spec), self.assertRaises(ValueError):
                parse_excluded_pages(spec, 6)
            with self.subTest(spec=spec), self.assertRaises(ValueError):
                parse_page_order(spec, 6)

    def test_empty_order_slots_and_job_limit(self):
        for spec, total in [("1,,2", 5), ("1-10001", 10001)]:
            with self.assertRaises(ValueError):
                parse_page_order(spec, total)


class PrinterTests(unittest.TestCase):
    def test_copies_paper_and_duplex_share_one_settings_flag(self):
        command = build_print_command(
            "SumatraPDF.exe", "prepared.pdf", "Office printer", "A3", 3, True
        )
        self.assertEqual(command.count("-print-settings"), 1)
        settings = command[command.index("-print-settings") + 1].split(",")
        self.assertEqual(set(settings), {"noscale", "3x", "paper=A3", "duplex"})
        self.assertEqual(command[1:3], ["-print-to", "Office printer"])

    def test_booklet_short_edge_and_letter_paper(self):
        command = build_print_command(
            "SumatraPDF.exe", "prepared.pdf", paper="Carta", booklet=True
        )
        self.assertIn("-print-to-default", command)
        self.assertIn("duplexshort", command[3])
        self.assertIn("paper=Letter", command[3])

    def test_invalid_copies(self):
        for copies in (0, -1, 10000):
            with self.assertRaises(ValueError):
                build_print_command("sumatra", "file.pdf", copies=copies)


class CliTests(unittest.TestCase):
    def test_windows_entry_points_dispatch_without_starting_tk(self):
        from grafiplot.cli import main

        for args, action, paths in [
            (["one.pdf"], "open_paths", ["one.pdf"]),
            (["--convertir", "one.png"], "convert_single", ["one.png"]),
            (
                ["--combinar", "one.pdf", "two.pdf"],
                "combine_files",
                ["one.pdf", "two.pdf"],
            ),
            (["--combinar"], "combine_files", None),
        ]:
            with self.subTest(args=args), patch("grafiplot.cli.App") as app:
                main(args)
                app.return_value.after.call_args.args[1]()
                getattr(app.return_value, action).assert_called_once_with(paths)
                app.return_value.mainloop.assert_called_once()


if __name__ == "__main__":
    unittest.main()
