"""Read-only printer validation and persistent local print diagnostics."""

import datetime
import json
import os
import uuid
from pathlib import Path

from grafiplot.core.printing import DEFAULT_PRINTER


def printer_details(printer):
    if os.name != "nt":
        return {"name": printer, "status": 0, "duplex": None}
    import win32print

    if printer == DEFAULT_PRINTER:
        try:
            printer = win32print.GetDefaultPrinter()
        except Exception as error:
            raise ValueError(
                "Windows no tiene una impresora predeterminada disponible. Seleccione una impresora por su nombre."
            ) from error
    try:
        handle = win32print.OpenPrinter(printer)
        try:
            details = win32print.GetPrinter(handle, 2)
        finally:
            win32print.ClosePrinter(handle)
    except Exception as error:
        raise ValueError(
            f"Windows no pudo abrir la impresora «{printer}». Actualice la lista o revise su instalación. Detalle: {error}"
        ) from error
    duplex = None
    try:
        capability = win32print.DeviceCapabilities(
            printer, details.get("pPortName", ""), 7
        )  # DC_DUPLEX
        duplex = bool(capability) if capability in (0, 1) else None
    except Exception:
        pass
    return {
        "name": printer,
        "status": details.get("Status", 0),
        "duplex": duplex,
        "port": details.get("pPortName", ""),
        "driver": details.get("pDriverName", ""),
    }


def default_log_directory():
    return (
        Path(os.environ.get("LOCALAPPDATA", Path.home())) / "GRAFIPLOT Studio" / "logs"
    )


def write_diagnostic(directory, record):
    """Logging must never turn a successful submission into an apparent failure."""
    try:
        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / (
            "impresion_"
            + datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            + "_"
            + uuid.uuid4().hex[:6]
            + ".json"
        )
        path.write_text(
            json.dumps(
                {
                    "date": datetime.datetime.now().isoformat(timespec="seconds"),
                    **record,
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        return str(path)
    except OSError:
        return None


def process_text(value):
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")[-4000:]
    return value[-4000:] if isinstance(value, str) else ""


def error_reason(code):
    status = code & 0xFFFFFFFF
    return {
        0xC0000135: "Windows no pudo cargar una biblioteca necesaria para SumatraPDF.",
        0xC0000142: "Windows no pudo inicializar SumatraPDF o su controlador.",
        0xC000007B: "Windows detectó una biblioteca incompatible al iniciar SumatraPDF.",
        0xC0000005: "SumatraPDF o el controlador se cerró por un fallo de acceso a memoria.",
    }.get(
        status,
        "SumatraPDF no confirmó el envío. Puede ser un fallo del controlador, del papel o del dúplex; el código no identifica por sí solo la causa.",
    )
