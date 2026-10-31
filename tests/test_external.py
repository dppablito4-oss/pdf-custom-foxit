"""External process environment and loader regression checks; never prints."""

import ctypes
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from grafiplot.core.external import system_dll_search, system_environment
from grafiplot.desktop.printer_support import error_reason, write_diagnostic


class ExternalTests(unittest.TestCase):
    def test_only_private_bundle_directories_are_removed_from_child_path(self):
        with tempfile.TemporaryDirectory() as folder:
            private = Path(folder) / "bundle"
            system = Path(folder) / "system"
            value = os.pathsep.join([str(private), str(private / "dlls"), str(system)])
            with (
                patch.object(sys, "_MEIPASS", str(private), create=True),
                patch.dict(os.environ, {"PATH": value}),
            ):
                child = system_environment()
                self.assertEqual(child["PATH"], str(system))
                self.assertEqual(os.environ["PATH"], value)

    @unittest.skipUnless(sys.platform == "win32", "Windows loader behavior")
    def test_private_dll_directory_is_reset_and_restored_after_failure(self):
        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel.GetDllDirectoryW.argtypes = [ctypes.c_uint32, ctypes.c_wchar_p]
        kernel.SetDllDirectoryW.argtypes = [ctypes.c_wchar_p]

        def current():
            buffer = ctypes.create_unicode_buffer(32768)
            kernel.GetDllDirectoryW(len(buffer), buffer)
            return buffer.value

        old = current()
        with tempfile.TemporaryDirectory() as folder:
            try:
                kernel.SetDllDirectoryW(folder)
                with patch.object(sys, "frozen", True, create=True):
                    with self.assertRaisesRegex(RuntimeError, "child failed"):
                        with system_dll_search():
                            self.assertEqual(current(), "")
                            raise RuntimeError("child failed")
                self.assertEqual(current(), folder)
            finally:
                kernel.SetDllDirectoryW(old or None)

    def test_known_loader_crash_is_distinguished_from_generic_print_failure(self):
        self.assertIn("biblioteca", error_reason(0xC0000135))
        self.assertIn("biblioteca", error_reason(0xC0000135 - 2**32))
        self.assertIn("no identifica por sí solo", error_reason(1))

    def test_unwritable_diagnostics_do_not_mask_the_print_result(self):
        with tempfile.TemporaryDirectory() as folder:
            occupied = Path(folder) / "file"
            occupied.write_text("preserve", encoding="utf-8")
            self.assertIsNone(write_diagnostic(occupied, {"returncode": 1}))


if __name__ == "__main__":
    unittest.main()
