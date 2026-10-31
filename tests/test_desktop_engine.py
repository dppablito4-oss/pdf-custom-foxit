"""Integration tests for the headless Tauri engine and its JSON wire protocol."""

import base64
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pymupdf as fitz

from grafiplot.desktop.engine import Engine
from tests.test_core import sample_pdf


class DesktopEngineTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="grafiplot_desktop_test_")
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)
        self.source = sample_pdf(self.folder / "test.pdf", 5)
        self.original = hashlib.sha256(Path(self.source).read_bytes()).digest()
        self.engine = Engine()
        self.engine.log_directory = self.folder / "logs"
        self.enterContext(
            patch(
                "grafiplot.desktop.printing.printer_details",
                side_effect=lambda name: {"name": name, "duplex": True, "status": 0},
            )
        )
        self.addCleanup(self.engine.close)
        self.doc = self.engine.call("open", {"paths": [self.source]})["documents"][0]
        self.settings = {"mode": "normal", "paper": "A4 (210 × 297 mm)", "copies": 1}

    def tearDown(self):
        self.assertEqual(
            hashlib.sha256(Path(self.source).read_bytes()).digest(), self.original
        )

    def test_headless_protocol_does_not_import_tkinter(self):
        script = 'from grafiplot.desktop.engine import Engine; import sys; assert "tkinter" not in sys.modules'
        subprocess.run([sys.executable, "-c", script], check=True, capture_output=True)

    def test_render_and_prepared_output(self):
        for mode, count in [("normal", 5), ("poster", 20), ("booklet", 4), ("nup", 3)]:
            with self.subTest(mode=mode):
                preview = self.engine.prepare(
                    self.doc["id"], {**self.settings, "mode": mode}
                )
                self.assertEqual(preview["pages"], count)
                image = self.engine.render(self.doc["id"], preview=True, width=200)
                self.assertTrue(image["image"].startswith("data:image/png;base64,"))
                self.assertEqual(image["pages"], count)

    def test_selection_export_and_overwrite_guard(self):
        result = self.engine.export(
            self.doc["id"], {**self.settings, "order": "3,1,1", "excluded": "2"}
        )
        with fitz.open(stream=base64.b64decode(result["data"]), filetype="pdf") as pdf:
            self.assertEqual(
                [page.get_text().strip() for page in pdf],
                ["PAGE 3", "PAGE 1", "PAGE 1"],
            )
        with self.assertRaises(ValueError):
            self.engine.export(self.doc["id"], self.settings, self.source)

    def test_edit_rotate_delete_and_crop(self):
        self.engine.edit(self.doc["id"], "rotate", [0])
        self.assertEqual(self.engine.documents[self.doc["id"]]["pdf"][0].rotation, 90)
        updated = self.engine.edit(self.doc["id"], "delete", [1, 2])
        self.assertEqual(updated["pages"], 3)
        self.engine.edit(self.doc["id"], "crop", crop=[0.1, 0.1, 0.9, 0.9])
        self.assertEqual(len(self.engine.documents[self.doc["id"]]["crops"]), 3)
        self.engine.prepare(self.doc["id"], self.settings)
        self.engine.edit(self.doc["id"], "clear_crop")
        self.assertFalse(self.engine.documents[self.doc["id"]]["crops"])
        with self.assertRaises(ValueError):
            self.engine.edit(self.doc["id"], "delete", [0, 1, 2])

    def test_merge_uses_edits_and_preserves_originals(self):
        second = self.engine.open([sample_pdf(self.folder / "second.pdf", 2)])[
            "documents"
        ][0]
        self.engine.edit(self.doc["id"], "delete", [1, 2, 3, 4])
        merged = self.engine.merge([second["id"], self.doc["id"]], duplex=True)
        self.assertEqual(merged["pages"], 6)

    def test_upload_is_real_document(self):
        result = self.engine.upload(
            [
                {
                    "name": "archivo español.pdf",
                    "data": base64.b64encode(Path(self.source).read_bytes()).decode(),
                }
            ]
        )
        self.assertEqual(result["documents"][0]["name"], "archivo español.pdf")
        self.assertEqual(result["documents"][0]["pages"], 5)

    def test_report_returns_a4_pdf(self):
        self.engine.jobs.append(
            {"client": "Cliente", "name": "Documento", "sheets": 3, "cost": 0.3}
        )
        result = self.engine.report("Cliente")
        with fitz.open(stream=base64.b64decode(result["data"]), filetype="pdf") as pdf:
            self.assertIn("Cliente", pdf[0].get_text())
            self.assertIn("3 hojas", pdf[0].get_text())

    def test_invalid_settings(self):
        for patch_settings in [
            {"margin": 300},
            {"columns": 900, "mode": "poster"},
            {"content": 999},
            {"copies": 0},
            {"mode": "unknown"},
        ]:
            with self.subTest(settings=patch_settings), self.assertRaises(ValueError):
                self.engine.prepare(self.doc["id"], {**self.settings, **patch_settings})

    def test_print_uses_checked_subprocess_without_real_printer(self):
        with (
            patch(
                "grafiplot.desktop.printing.find_sumatra", return_value="sumatra.exe"
            ),
            patch("grafiplot.desktop.printing.subprocess.run") as run,
        ):
            run.return_value.returncode = 0
            result = self.engine.print_document(
                self.doc["id"], self.settings, "Test printer", "Client"
            )
            self.assertEqual(result["jobs"][0]["client"], "Client")
            self.assertEqual(run.call_args.args[0].count("-print-settings"), 1)

    def test_named_a4_duplex_is_sent_to_the_selected_printer(self):
        with (
            patch(
                "grafiplot.desktop.printing.find_sumatra", return_value="sumatra.exe"
            ),
            patch("grafiplot.desktop.printing.subprocess.run") as run,
        ):
            run.return_value.returncode = 0
            self.engine.print_document(
                self.doc["id"], {**self.settings, "duplex": True}, "Selected HP"
            )
            command = run.call_args.args[0]
            self.assertEqual(command[1:3], ["-print-to", "Selected HP"])
            self.assertNotIn("-print-to-default", command)
            options = command[command.index("-print-settings") + 1].split(",")
            self.assertIn("paper=A4", options)
            self.assertIn("duplex", options)

    def test_default_alias_is_resolved_before_submitting_and_recording(self):
        with (
            patch(
                "grafiplot.desktop.printing.find_sumatra", return_value="sumatra.exe"
            ),
            patch(
                "grafiplot.desktop.printing.printer_details",
                return_value={
                    "name": "Windows default HP",
                    "duplex": True,
                    "status": 0,
                },
            ),
            patch("grafiplot.desktop.printing.subprocess.run") as run,
        ):
            run.return_value.returncode = 0
            result = self.engine.print_document(self.doc["id"], self.settings)
            self.assertEqual(
                run.call_args.args[0][1:3], ["-print-to", "Windows default HP"]
            )
            self.assertEqual(result["jobs"][0]["printer"], "Windows default HP")

    def test_failed_print_keeps_exit_code_and_local_diagnostics_without_retrying(self):
        with (
            patch(
                "grafiplot.desktop.printing.find_sumatra", return_value="sumatra.exe"
            ),
            patch("grafiplot.desktop.printing.subprocess.run") as run,
        ):
            run.return_value.returncode = 1
            run.return_value.stderr = b"Printer initialization failed"
            run.return_value.stdout = b""
            with self.assertRaisesRegex(RuntimeError, "Selected HP.*Código 1"):
                self.engine.print_document(
                    self.doc["id"], {**self.settings, "duplex": True}, "Selected HP"
                )
            run.assert_called_once()
            self.assertFalse(self.engine.jobs)
            logs = list(self.engine.log_directory.glob("*.json"))
            self.assertEqual(len(logs), 1)
            record = json.loads(logs[0].read_text(encoding="utf-8"))
            self.assertEqual(record["printer"], "Selected HP")
            self.assertEqual(record["returncode"], 1)
            self.assertTrue(record["duplex"])
            self.assertIn("initialization", record["stderr"])

    def test_unsupported_duplex_does_not_launch_sumatra(self):
        with (
            patch(
                "grafiplot.desktop.printing.find_sumatra", return_value="sumatra.exe"
            ),
            patch(
                "grafiplot.desktop.printing.printer_details",
                return_value={"name": "Simplex printer", "duplex": False, "status": 0},
            ),
            patch("grafiplot.desktop.printing.subprocess.run") as run,
        ):
            with self.assertRaisesRegex(ValueError, "no admite doble cara"):
                self.engine.print_document(
                    self.doc["id"], {**self.settings, "duplex": True}, "Simplex printer"
                )
            run.assert_not_called()

    def test_print_timeout_does_not_retry_or_record_success(self):
        with (
            patch(
                "grafiplot.desktop.printing.find_sumatra", return_value="sumatra.exe"
            ),
            patch(
                "grafiplot.desktop.printing.subprocess.run",
                side_effect=subprocess.TimeoutExpired("sumatra", 180),
            ) as run,
        ):
            with self.assertRaisesRegex(
                RuntimeError, "Revise la cola antes de repetir"
            ):
                self.engine.print_document(self.doc["id"], self.settings, "Selected HP")
            run.assert_called_once()
            self.assertFalse(self.engine.jobs)

    def test_unknown_command_and_closed_document(self):
        with self.assertRaises(ValueError):
            self.engine.call("execute", {})
        self.engine.close_document(self.doc["id"])
        with self.assertRaises(ValueError):
            self.engine.render(self.doc["id"])

    @unittest.skipUnless(sys.platform == "win32", "Windows printer dialogs")
    def test_native_driver_preferences_and_properties_use_distinct_commands(self):
        with patch("grafiplot.desktop.printing.subprocess.Popen") as launch:
            self.engine.printer_dialog("Selected HP", properties=False)
            self.engine.printer_dialog("Selected HP", properties=True)
            self.assertEqual(
                launch.call_args_list[0].args[0],
                ["rundll32.exe", "printui.dll,PrintUIEntry", "/e", "/n", "Selected HP"],
            )
            self.assertEqual(
                launch.call_args_list[1].args[0],
                ["rundll32.exe", "printui.dll,PrintUIEntry", "/p", "/n", "Selected HP"],
            )

    def test_stdio_returns_one_json_response_per_request(self):
        process = subprocess.run(
            [sys.executable, "-u", "-m", "grafiplot.desktop.service"],
            input=json.dumps({"method": "open", "params": {"paths": [self.source]}})
            + "\n"
            + json.dumps({"method": "bogus"})
            + "\n",
            text=True,
            capture_output=True,
            timeout=30,
        )
        self.assertEqual(process.returncode, 0)
        responses = [json.loads(line) for line in process.stdout.splitlines()]
        self.assertEqual(len(responses), 2)
        self.assertEqual(responses[0]["result"]["documents"][0]["pages"], 5)
        self.assertIn("error", responses[1])

    def test_shutdown_exits_cleanly(self):
        process = subprocess.run(
            [sys.executable, "-u", "-m", "grafiplot.desktop.service"],
            input='{"method":"shutdown"}\n',
            encoding="utf-8",
            capture_output=True,
            timeout=15,
        )
        self.assertEqual(process.returncode, 0)
        self.assertEqual(process.stdout, "")


if __name__ == "__main__":
    unittest.main()
