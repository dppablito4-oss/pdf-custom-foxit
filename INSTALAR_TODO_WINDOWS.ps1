$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
if (-not (Test-Path -LiteralPath (Join-Path $PSScriptRoot 'grafiplot\application.py'))) {
    throw 'Falta la carpeta grafiplot. Extraiga todos los archivos del proyecto antes de instalar.'
}
function Find-Python {
    if (Get-Command py -ErrorAction SilentlyContinue) {
        $list = & py -3 -c "import sys; print(sys.executable)" 2>$null
        if ($LASTEXITCODE -eq 0 -and $list) { return @('py','-3') }
    }
    if (Get-Command python -ErrorAction SilentlyContinue) {
        & python -c "import sys; print(sys.version_info.major)" 2>$null | Out-Null
        if ($LASTEXITCODE -eq 0) { return @('python') }
    }
    return $null
}
function Find-LibreOffice {
    $found = Get-Command soffice -ErrorAction SilentlyContinue
    if ($found) { return $true }
    return ((Test-Path 'C:\Program Files\LibreOffice\program\soffice.exe') -or (Test-Path 'C:\Program Files (x86)\LibreOffice\program\soffice.exe'))
}
Write-Host '==== GRAFIPLOT PDF PRINT - Estudio de impresion ====' -ForegroundColor Red
Write-Host 'Se instalaran solo componentes necesarios desde fuentes oficiales; requiere internet.'
$py = Find-Python
if (-not $py) {
    if (-not (Get-Command winget -ErrorAction SilentlyContinue)) { throw 'No se encontro winget. Instale Python 3.12 desde python.org y vuelva a ejecutar.' }
    Write-Host 'Instalando Python con winget...' -ForegroundColor Yellow
    & winget install --id Python.Python.3.12 --exact --source winget --accept-source-agreements --accept-package-agreements --silent
    if ($LASTEXITCODE -ne 0) { throw 'Fallo la instalacion automatica de Python.' }
    $env:Path = "$env:LOCALAPPDATA\Programs\Python\Python312;$env:LOCALAPPDATA\Programs\Python\Python312\Scripts;$env:Path"
    $py = Find-Python
    if (-not $py) { throw 'Python instalado pero no detectado. Cierre y vuelva a abrir este instalador.' }
}
if (-not (Find-LibreOffice)) {
    if (-not (Get-Command winget -ErrorAction SilentlyContinue)) { throw 'Para Word/Excel/PowerPoint se requiere LibreOffice. Instale desde libreoffice.org.' }
    Write-Host 'Instalando LibreOffice para abrir Word, Excel y PowerPoint...' -ForegroundColor Yellow
    & winget install --id TheDocumentFoundation.LibreOffice --exact --source winget --accept-source-agreements --accept-package-agreements --silent
    if ($LASTEXITCODE -ne 0) { throw 'No se pudo instalar LibreOffice automaticamente.' }
}
if (-not (Test-Path '.venv\Scripts\python.exe')) {
    Write-Host 'Preparando entorno Python...' -ForegroundColor Yellow
    if ($py.Count -eq 2) { & $py[0] $py[1] -m venv .venv }
    else { & $py[0] -m venv .venv }
    if ($LASTEXITCODE -ne 0) { throw 'No se pudo preparar el entorno Python.' }
}
Write-Host 'Instalando librerias...' -ForegroundColor Yellow
& '.\.venv\Scripts\python.exe' -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) { throw 'No se pudo actualizar pip.' }
& '.\.venv\Scripts\python.exe' -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) { throw 'No se pudieron instalar las dependencias.' }
Write-Host 'Instalacion completada.' -ForegroundColor Green

# SumatraPDF para imprimir directamente en impresoras elegidas (incluidos reportes).
$sumatra = @('C:\Program Files\SumatraPDF\SumatraPDF.exe', 'C:\Program Files (x86)\SumatraPDF\SumatraPDF.exe', "$env:LOCALAPPDATA\SumatraPDF\SumatraPDF.exe")
if (-not (Get-Command SumatraPDF.exe -ErrorAction SilentlyContinue) -and -not ($sumatra | Where-Object { Test-Path $_ })) {
    if (Get-Command winget -ErrorAction SilentlyContinue) {
        Write-Host 'Instalando SumatraPDF para impresion directa...' -ForegroundColor Yellow
        & winget install --id SumatraPDF.SumatraPDF --exact --source winget --accept-source-agreements --accept-package-agreements --silent
        if ($LASTEXITCODE -ne 0) { Write-Warning 'SumatraPDF no se instalo; los reportes PDF siguen disponibles para impresion manual.' }
    }
}
