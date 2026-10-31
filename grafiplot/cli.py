"""Command-line entry point used by Windows shortcuts and context menus."""

import argparse

from grafiplot.application import App


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="GRAFIPLOT PDF PRINT — Estudio de impresión"
    )
    actions = parser.add_mutually_exclusive_group()
    actions.add_argument(
        "--convertir", action="store_true", help="Convertir archivos a PDF"
    )
    actions.add_argument(
        "--combinar", action="store_true", help="Abrir el organizador de combinación"
    )
    parser.add_argument(
        "archivos", nargs="*", help="Documentos para abrir, convertir o combinar"
    )
    args = parser.parse_args(argv)
    app = App()
    if args.convertir:
        app.after(350, lambda: app.convert_single(args.archivos))
    elif args.combinar:
        app.after(350, lambda: app.combine_files(args.archivos or None))
    elif args.archivos:
        app.after(350, lambda: app.open_paths(args.archivos))
    app.mainloop()
