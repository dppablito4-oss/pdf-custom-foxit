# GRAFIPLOT Studio · escritorio con Tauri

La aplicación nueva utiliza **React + TypeScript + Vite + Tauri 2**. El ejecutable final no utiliza Tkinter ni necesita Python o Node instalados en el equipo del usuario.

## Ejecutables

`python scripts/build_desktop.py` genera en `artifacts/`:

- Un instalador `.exe` NSIS por usuario. Instala la aplicación, el motor PDF y los accesos de Windows.
- `GRAFIPLOT-Studio-<versión>-portable.zip`, con la aplicación y `grafiplot-engine.exe`. Conserva ambos archivos juntos para usar la versión portable. La carpeta de salida incluye la versión para no reemplazar otras copias en uso.

No se distribuyen lanzadores `.bat`. El motor Python se incluye como un ejecutable auxiliar empaquetado con PyInstaller. Tauri lo inicia sin ventana de consola.

## Preparar el entorno

Para compilar en Windows se necesitan Node 22.12 o posterior, Python 3.11 o posterior, Rust estable con destino MSVC, Microsoft C++ Build Tools y Windows SDK. WebView2 se utiliza para renderizar la interfaz. El instalador de Tauri comprueba su disponibilidad.

```powershell
python -m pip install -r requirements-build.txt
npm ci
```

Rust está normalmente en `%USERPROFILE%\.cargo\bin`. Si no aparece en PATH:

```powershell
$env:PATH = "$env:USERPROFILE\.cargo\bin;$env:PATH"
```

## Desarrollo

```powershell
npm run desktop:dev
```

Tauri abre la ventana y Vite actualiza los componentes al editarlos. En desarrollo, el motor se inicia con `python -m grafiplot.desktop.service`. Puedes indicar otro Python mediante `GRAFIPLOT_PYTHON`.

Para probar la interfaz en un navegador con el motor PDF real:

```powershell
npm run dev
```

Abre `http://127.0.0.1:1420`. El modo navegador permite cargar archivos y descargar resultados. El modo escritorio utiliza los diálogos nativos y rutas locales.

## Compilar

```powershell
python scripts/build_desktop.py
```

Este comando empaqueta Python/PyMuPDF, compila TypeScript, genera los assets con Vite y compila Tauri y el instalador NSIS. La primera compilación descarga dependencias Rust y tarda más. Los ejecutables no se firman automáticamente; configura un certificado de firma para una distribución comercial firmada.

## Estructura

| Ubicación | Responsabilidad |
| --- | --- |
| `src/components/` | Paneles y vistas React |
| `src/components/EditorHeader.tsx`, `EditorDialogs.tsx` | Barra superior de herramientas y diálogos del editor |
| `src/components/PageRail.tsx`, `src/hooks/useMarqueeSelection.ts` | Panel redimensionable, selección rectangular y autodesplazamiento |
| `src/hooks/useStudio.ts` | Estado de documentos y acciones de la sesión |
| `src/lib/engine.ts` | Transporte, diálogos nativos y descargas de desarrollo |
| `src/types.ts` | Contratos de datos y valores iniciales |
| `src/styles.css` | Diseño visual adaptable |
| `src/editor.css` | Distribución compacta del editor, cinta superior y jerarquía de impresión |
| `src/appearance.css`, `src/hooks/useAppearance.ts` | Paletas claro/oscuro, tipografía y preferencia persistente |
| `src-tauri/src/main.rs` | Ventana, proceso auxiliar y comunicación por stdin/stdout |
| `src-tauri/tauri.conf.json` | Configuración del instalador y la aplicación |
| `grafiplot/desktop/engine.py` | Sesión y despacho de comandos sin Tkinter |
| `grafiplot/desktop/documents.py` | Apertura, edición y combinación |
| `grafiplot/desktop/output.py` | Validación, vista previa y exportación |
| `grafiplot/desktop/printing.py` | Impresoras, configuración y reportes |
| `grafiplot/core/` | Motor PDF compartido, independiente de la interfaz |

El transporte de producción es JSON Lines entre Rust y Python; no abre un servidor HTTP ni expone comandos del shell a React. Los cambios de configuración conservan el estado de cada pestaña y preparan una nueva salida tras una breve pausa. Las miniaturas se solicitan cuando entran en la zona visible.

## Editor compacto · 1.2

Abrir queda junto al título; guardar, imprimir, selección, recorte y giro se agrupan arriba. Los mensajes de éxito se muestran en la barra de estado. Los errores se muestran en una franja inferior que puede cerrarse. La pantalla vacía no incluye anuncios ni llamadas grandes a abrir archivos.

En el panel de páginas, arrastra el separador vertical para cambiar el ancho; un doble clic restaura el ancho inicial. El ancho se guarda entre sesiones y se ajusta al espacio disponible. El control de tamaño permite cambiar las miniaturas; el panel distribuye tantas columnas como quepan.

Arrastra desde un espacio vacío entre miniaturas para seleccionar un rectángulo. Si mantienes Ctrl se añade a la selección. La selección se desplaza automáticamente al llegar a los bordes. También funcionan Ctrl+clic, Shift+clic, Ctrl+A, Escape y las flechas de dirección. Las operaciones de giro o eliminación se aplican a la selección.

La cabecera de impresora destaca el destino y abre directamente las **Preferencias del driver** (`PrintUIEntry /e`) o sus **Propiedades** (`/p`). Papel, calidad, intensidad y tipos de acabado disponibles dependen del controlador instalado. No se cambian ajustes del controlador automáticamente al abrirlo.

`python -m tests.editor_smoke` comprueba redimensión, varias columnas, selección rectangular, Ctrl/Shift, teclado, autodesplazamiento, ventana compacta y solicitudes a ambos diálogos nativos. Intercepta esas solicitudes; no abre diálogos de impresora ni imprime durante la prueba.

## Pruebas

```powershell
python -m unittest discover -s tests -v
npm test
npm run build
```

Con `npm run dev` iniciado:

```powershell
python -m tests.web_smoke
```

Las pruebas de navegador generan capturas en `artifacts/screenshots/`. Usan PDFs sintéticos y no imprimen. Las pruebas de solicitudes de impresión sustituyen el proceso de SumatraPDF.

`python -m tests.appearance_smoke` verifica ambos temas, la persistencia de la elección, un contraste mínimo de 4.5:1 en controles principales y ventanas compactas. Para recompilar únicamente cambios de interfaz con el motor ya empaquetado: `python scripts/build_desktop.py --reuse-engine`.

## Complementos

El motor PDF se incluye. LibreOffice para documentos Office, SumatraPDF para impresión directa y 7-Zip/WinRAR para RAR siguen siendo complementos externos. Los reportes e historial corresponden a la sesión actual; las asignaciones de impresora se guardan en `~/grafiplot_pdf_print_ajustes.json`.

Los módulos Tkinter anteriores permanecen en el repositorio como referencia y para comparación de regresiones. No forman parte del ejecutable Tauri. La entrada principal de desarrollo del nuevo escritorio es `npm run desktop:dev`.

## Diagnóstico de impresión · 1.1.1

La selección manual se envía por nombre a SumatraPDF. «Predeterminada» se resuelve al nombre de la impresora de Windows antes de enviar. El motor consulta el controlador y avisa si este informa que no admite doble cara automática. No cambia a una cara ni reintenta automáticamente.

Al fallar SumatraPDF, el aviso muestra impresora, código de salida y ruta del diagnóstico local en `%LOCALAPPDATA%\GRAFIPLOT Studio\logs\`. El código 1 es genérico y no prueba por sí solo una causa. El registro conserva papel, dúplex, controlador y salida del proceso; no incluye el contenido del PDF. Los avisos de error permanecen hasta cerrarlos.

El motor empaquetado restaura temporalmente la búsqueda de bibliotecas de Windows al invocar SumatraPDF o LibreOffice, para que no hereden las bibliotecas privadas de PyInstaller. No modifica la configuración del sistema.

`python -m tests.print_request_smoke` verifica en navegador que la impresora elegida, A4 y dúplex llegan a la solicitud. Intercepta el envío y no imprime.

Referencias oficiales: [Tauri sidecars](https://v2.tauri.app/develop/sidecar/), [requisitos de Windows](https://v2.tauri.app/start/prerequisites/), [instalador Windows](https://v2.tauri.app/distribute/windows-installer/).
