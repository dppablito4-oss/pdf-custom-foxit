# Arquitectura y guía de cambios

> Esta guía describe la implementación Tkinter anterior, conservada como referencia. El escritorio principal utiliza React/Vite/Tauri; consulta [DESKTOP.md](DESKTOP.md).

`app.py` es únicamente la entrada compatible con los accesos directos y el menú contextual. La aplicación se compone en `grafiplot/application.py`.

```text
app.py / python -m grafiplot
└── cli.py
    └── application.App
        ├── ui/           construcción de paneles, estilos y eventos
        ├── features/     flujos de documentos, páginas, impresión y reportes
        └── core/         operaciones sobre PDF y archivos, sin Tkinter
```

## Responsabilidades

`ui/layout.py` compone la cabecera, el panel lateral y el área de trabajo. Los constructores de paneles reciben `app`, crean widgets y conectan acciones. `ui/theme.py` centraliza la paleta y los estilos ttk. `ui/settings.py` controla qué opciones se muestran y valida los parámetros de salida.

`features/` conserva los manejadores de cada flujo. Se integran como mixins explícitos en `App`, una migración incremental que mantiene los eventos existentes. Comparten el estado de `App` y los callbacks de la ventana; no hay carga dinámica de métodos ni importaciones circulares entre funcionalidades. Cada archivo declara sus importaciones.

`core/` no importa Tkinter. Las funciones reciben rutas, documentos o parámetros y devuelven resultados, o lanzan excepciones que la interfaz presenta al usuario:

| Módulo | Función |
| --- | --- |
| `archives.py` | Extraer documentos de ZIP/RAR con límites de cantidad y tamaño |
| `conversion.py` | Convertir imágenes, TIFF multipágina, Office y SVG a PDF |
| `merge.py` | Crear un destino nuevo, combinar, excluir y añadir separadores |
| `pages.py` | Validar rangos y orden de páginas antes de expandirlos |
| `selection.py` | Preparar una copia ordenada y recortada |
| `layout.py` | Generar salida normal, póster, folleto o varias páginas por hoja |
| `printing.py` | Localizar SumatraPDF y construir comandos sin ejecutarlos |

## Estado por documento

`features/documents.py` define `TAB_VARIABLES` para los valores Tk y `TAB_COLLECTIONS` para selección, recortes e historial. `_state()` toma una copia; `_restore()` restaura sin disparar un renderizado por cada variable y después programa una única preparación. Al añadir una opción por pestaña:

1. Declara su variable inicial en `application.py`.
2. Añádela a `TAB_VARIABLES` o `TAB_COLLECTIONS`.
3. Define su valor para documentos nuevos en `open_paths()`.
4. Conecta sus cambios en `ui/layout.py` o mediante el comando del control.
5. Verifica que se conserve al cambiar de pestaña.

Los objetos `document` y `preview_doc` son documentos PyMuPDF abiertos. El ciclo de vida se controla desde documentos y vista previa. Las funciones del núcleo cierran sus documentos incluso cuando la validación falla. Las tareas pendientes de Tk se cancelan al cerrar la aplicación.

## Flujo de salida

`ordered_page_ids()` resuelve orden explícito, selección y exclusiones. `selected_pdf()` crea una copia temporal con ese orden y sus recortes. `create_output()` aplica la distribución sobre esa copia. Exportación, vista previa e impresión comparten estas operaciones; la impresión construye su solicitud con `build_print_command()`.

El texto y los vectores se conservan en la composición PDF y los recortes rectangulares. Los recortes libres usan una máscara rasterizada. La vista previa y las miniaturas usan imágenes únicamente para mostrar el documento. Las páginas separadoras vacías se conservan.

## Pruebas y distribución

`tests/test_core.py` verifica salidas PDF reales, texto, tamaños, folletos, distribución, recortes, combinación, rangos, TIFF, extracción ZIP y solicitudes de impresión. También verifica el despacho de la línea de comandos sin iniciar Tk.

`tests/ui_smoke.py` instancia la aplicación para comprobar la restauración de pestañas, los modos, la edición y los límites de la ventana. Sustituye los avisos modales durante las pruebas y no llama a una impresora.

Al distribuir una nueva versión, incluye la carpeta `grafiplot/` completa. Ambos instaladores validan su presencia y el instalador con acceso directo la copia al destino. El archivo `app.py` conserva la entrada que utiliza `ACTIVAR_MENU_CLIC_DERECHO.ps1`.
