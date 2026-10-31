# GRAFIPLOT Studio

Estudio de impresión de escritorio con **React, TypeScript, Vite y Tauri 2**. Interfaz de diseño web, procesamiento PDF local y distribución como instalador `.exe` para Windows.

## Usar la aplicación

Abre el instalador en `artifacts/`. No necesitas instalar Python, Node o Rust para usar la aplicación compilada. También se genera `GRAFIPLOT-Studio-1.2.0-portable.zip`: extrae su contenido y abre `GRAFIPLOT Studio.exe`, conservando `grafiplot-engine.exe` en la misma carpeta. Los portables nuevos se guardan en carpetas por versión para conservar las copias anteriores que estén en uso.

La entrega no utiliza archivos `.bat`.

La versión **1.2** organiza las herramientas en una barra superior compacta y destaca la configuración de impresión con degradados. Incluye acceso directo a preferencias y propiedades del controlador. El panel de páginas es redimensionable, permite varias columnas y selección rectangular con autodesplazamiento. Los temas claro y oscuro se cambian en la esquina superior derecha y conservan la preferencia entre sesiones. Los PDF mantienen sus colores originales.

## Funciones

- Documentos en pestañas con ajustes independientes y asignación por cliente.
- Miniaturas, selección múltiple, giro, eliminación y recorte sobre copias de trabajo.
- Vista original y vista de impresión, zoom y navegación de páginas.
- Modos normal, póster, folleto y varias páginas por hoja.
- Papel personalizado, márgenes, escala, copias, doble cara, orden y exclusiones.
- Combinación ordenada con exclusiones, separadores y preparación dúplex.
- Exportación PDF e impresión directa; reporte A4 e historial de la sesión.
- Preferencias y asignación automática de impresora según el papel.

Los originales permanecen intactos. La preparación de impresión conserva texto y vectores PDF.

## Desarrollo

```powershell
python -m pip install -r requirements-build.txt
npm ci
npm run desktop:dev
```

Para trabajar en la interfaz en un navegador con el motor PDF real:

```powershell
npm run dev
```

Abre `http://127.0.0.1:1420`. Este servidor solo se usa en desarrollo. El ejecutable final se comunica con el motor PDF por stdin/stdout.

## Generar el instalador y el portable

Necesitas Rust MSVC, Microsoft C++ Build Tools y Windows SDK en la máquina de compilación. Si Rust no está en PATH:

```powershell
$env:PATH = "$env:USERPROFILE\.cargo\bin;$env:PATH"
python scripts/build_desktop.py
```

La salida se copia a `artifacts/`. Lee [la guía del escritorio](docs/DESKTOP.md) para los requisitos, los comandos y la distribución.

## Módulos

| Carpeta | Responsabilidad |
| --- | --- |
| `src/components/` | Interfaz React por paneles y vistas |
| `src/hooks/` | Estado, preparación de salida y acciones |
| `src/lib/` | Comunicación, diálogos y selección |
| `src/styles.css` | Diseño visual |
| `src-tauri/` | Ventana nativa, comunicación Rust e instalador |
| `grafiplot/desktop/` | Motor de sesión sin Tkinter, separado por responsabilidades |
| `grafiplot/core/` | Conversión, selección, combinación y composición PDF |
| `scripts/` | Compilación y empaquetado |
| `tests/` | Pruebas PDF, motor de escritorio y navegador |

La implementación Tkinter anterior permanece como referencia para comparar regresiones. No se incluye en el ejecutable de Tauri. Sus antiguos scripts de instalación PowerShell tampoco forman parte de la distribución nueva.

## Verificación

```powershell
python -m unittest discover -s tests -v
npm test
npm run build
```

Con Vite iniciado: `python -m tests.web_smoke`. Las capturas quedan en `artifacts/screenshots/`. Las pruebas utilizan PDFs sintéticos y no envían trabajos a impresoras.

## Complementos

El motor PDF y sus bibliotecas se empaquetan con la aplicación. Word/Excel/PowerPoint requieren LibreOffice; la impresión directa requiere SumatraPDF y una impresora de Windows. RAR requiere 7-Zip o WinRAR. Los ajustes de impresoras se guardan en `~/grafiplot_pdf_print_ajustes.json`.

Los precios son referencias por hoja física en soles, editables en `grafiplot/constants.py`. El estado «enviado» no confirma salida física. El historial corresponde a la sesión actual.

Arquitectura de empaquetado basada en la [documentación oficial de Tauri](https://v2.tauri.app/develop/sidecar/). Los requisitos de compilación de Windows están en [Tauri Prerequisites](https://v2.tauri.app/start/prerequisites/).
