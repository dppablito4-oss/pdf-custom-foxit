$ErrorActionPreference='Stop'
try {
$source=$PSScriptRoot
$dest=Join-Path $env:LOCALAPPDATA 'Programs\GRAFIPLOT PDF PRINT'
Write-Host 'Instalando GRAFIPLOT PDF PRINT 34.0...' -ForegroundColor Cyan
New-Item -ItemType Directory -Force -Path $dest | Out-Null
$package=Join-Path $source 'grafiplot'
if (-not (Test-Path -LiteralPath (Join-Path $package 'application.py'))) {
    throw 'Falta la carpeta grafiplot. Extraiga la distribucion completa antes de instalar.'
}
Copy-Item -LiteralPath (Join-Path $source 'app.py') -Destination $dest -Force
Copy-Item -LiteralPath $package -Destination $dest -Recurse -Force
Copy-Item -LiteralPath (Join-Path $source 'requirements.txt') -Destination $dest -Force
Copy-Item -LiteralPath (Join-Path $source 'GRAFIPLOT.ico') -Destination $dest -Force
$activate=Join-Path $dest 'ACTIVAR_MENU_CLIC_DERECHO.ps1'
Copy-Item (Join-Path $source 'ACTIVAR_MENU_CLIC_DERECHO.ps1') $activate -Force
$pyexe=Join-Path $dest '.venv\Scripts\python.exe'
$pyw=Join-Path $dest '.venv\Scripts\pythonw.exe'
if (-not (Test-Path $pyexe)) {
  $candidate=Get-Command py -ErrorAction SilentlyContinue
  if ($candidate) { & py -3 -m venv (Join-Path $dest '.venv') }
  elseif (Get-Command python -ErrorAction SilentlyContinue) { & python -m venv (Join-Path $dest '.venv') }
  elseif (Get-Command winget -ErrorAction SilentlyContinue) {
      Write-Host 'Instalando Python (requiere Internet)...'
      & winget install --id Python.Python.3.12 --exact --source winget --accept-source-agreements --accept-package-agreements
      if ($LASTEXITCODE -ne 0) { throw 'No se pudo instalar Python automaticamente.' }
      $pythonUser=Join-Path $env:LOCALAPPDATA 'Programs\Python\Python312\python.exe'
      if (Test-Path $pythonUser) { & $pythonUser -m venv (Join-Path $dest '.venv') }
      else { throw 'Python se instalo pero Windows requiere reiniciar sesion. Vuelva a ejecutar INSTALAR_GRAFIPLOT.bat.' }
  } else { throw 'Instale Python 3.12 desde python.org (winget no esta disponible).' }
}
if (-not (Test-Path $pyexe)) { throw 'No se encontro Python en la carpeta de instalacion.' }
& $pyexe -m pip install -r (Join-Path $dest 'requirements.txt')
if ($LASTEXITCODE -ne 0) { throw 'Error al instalar las bibliotecas Python.' }
$launcher='"'+$pyw+'" "'+(Join-Path $dest 'app.py')+'"'
$ws=New-Object -ComObject WScript.Shell
$desktop=[Environment]::GetFolderPath('Desktop')
$shortcut=$ws.CreateShortcut((Join-Path $desktop 'GRAFIPLOT PDF PRINT.lnk'))
$shortcut.TargetPath=$pyw
$shortcut.Arguments='"'+(Join-Path $dest 'app.py')+'"'
$shortcut.WorkingDirectory=$dest
$shortcut.IconLocation=(Join-Path $dest 'GRAFIPLOT.ico')
$shortcut.Save()
# OpenWith registration: Windows 10 protects UserChoice; user selects default via Windows Settings.
$root=[Microsoft.Win32.Registry]::CurrentUser.CreateSubKey('Software\Classes\GrafiplotPDF.Document')
$root.SetValue('','GRAFIPLOT PDF PRINT')
$root.SetValue('FriendlyTypeName','Documento PDF - GRAFIPLOT')
$root.Close()
$sub=[Microsoft.Win32.Registry]::CurrentUser.CreateSubKey('Software\Classes\GrafiplotPDF.Document\DefaultIcon')
$sub.SetValue('',(Join-Path $dest 'GRAFIPLOT.ico'))
$sub.Close()
$sub=[Microsoft.Win32.Registry]::CurrentUser.CreateSubKey('Software\Classes\GrafiplotPDF.Document\shell\open\command')
$sub.SetValue('',$launcher+' "%1"')
$sub.Close()
$sub=[Microsoft.Win32.Registry]::CurrentUser.CreateSubKey('Software\Classes\.pdf\OpenWithProgids')
$sub.SetValue('GrafiplotPDF.Document','',[Microsoft.Win32.RegistryValueKind]::String)
$sub.Close()
& powershell -NoProfile -ExecutionPolicy Bypass -File $activate -InstallDir $dest
if ($LASTEXITCODE -ne 0) { Write-Warning 'Instalado, pero el menu clic derecho no pudo registrarse. Puede repetirlo desde la carpeta de instalacion.' }
Write-Host 'INSTALACION COMPLETADA. Icono creado en escritorio.' -ForegroundColor Green
Write-Host 'Para PDF predeterminado: Configuracion > Aplicaciones > Aplicaciones predeterminadas > Elegir por tipo de archivo > .pdf > GRAFIPLOT PDF PRINT.'
if (-not (Test-Path 'C:\Program Files\LibreOffice\program\soffice.exe') -and -not (Test-Path 'C:\Program Files (x86)\LibreOffice\program\soffice.exe')) {
 Write-Host 'Para abrir Word necesita instalar LibreOffice. Puede utilizar el archivo INSTALAR_COMPLEMENTOS_OPCIONALES.bat.' -ForegroundColor Yellow
}
} catch { Write-Host ('ERROR: '+$_.Exception.Message) -ForegroundColor Red;exit 1 }
