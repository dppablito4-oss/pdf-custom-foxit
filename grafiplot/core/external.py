"""Launch system programs without inheriting PyInstaller's private DLL search path.

https://pyinstaller.org/en/stable/common-issues-and-pitfalls.html#launching-external-programs-from-the-frozen-application
"""

import ctypes
import os
import sys
import threading
from contextlib import contextmanager
from pathlib import Path

_loader_lock = threading.RLock()


def system_environment():
    environment = os.environ.copy()
    bundle = getattr(sys, "_MEIPASS", None)
    if not bundle:
        return environment
    bundle = Path(bundle).resolve()
    entries = []
    for entry in environment.get("PATH", "").split(os.pathsep):
        try:
            if entry and Path(entry).resolve().is_relative_to(bundle):
                continue
        except (OSError, ValueError):
            pass
        entries.append(entry)
    environment["PATH"] = os.pathsep.join(entries)
    return environment


@contextmanager
def system_dll_search():
    """Restore the exact previous loader directory even if the child fails."""
    if sys.platform != "win32" or not getattr(sys, "frozen", False):
        yield
        return
    with _loader_lock:
        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel.GetDllDirectoryW.argtypes = [ctypes.c_uint32, ctypes.c_wchar_p]
        kernel.GetDllDirectoryW.restype = ctypes.c_uint32
        kernel.SetDllDirectoryW.argtypes = [ctypes.c_wchar_p]
        kernel.SetDllDirectoryW.restype = ctypes.c_int
        length = kernel.GetDllDirectoryW(0, None)
        buffer = ctypes.create_unicode_buffer(length + 1)
        kernel.GetDllDirectoryW(len(buffer), buffer)
        previous = buffer.value or None
        if not kernel.SetDllDirectoryW(None):
            raise ctypes.WinError(ctypes.get_last_error())
        try:
            yield
        finally:
            if not kernel.SetDllDirectoryW(previous):
                raise ctypes.WinError(ctypes.get_last_error())
