param([string]$InstallDir=$PSScriptRoot)
$ErrorActionPreference='Stop'
$app=Join-Path $InstallDir 'app.py'
$python=Join-Path $InstallDir '.venv\Scripts\pythonw.exe'
if(-not (Test-Path $python) -or -not (Test-Path $app) -or -not (Test-Path (Join-Path $InstallDir 'grafiplot\application.py'))){ throw 'No se encontraron app.py, la carpeta grafiplot y pythonw.exe en la instalacion.' }
$items=@(
@{id='GRAFI_Combinacion'; name='Combinar en PDF GRAFI'; arg='--combinar'},
@{id='GRAFI_Conversion'; name='Convertir a PDF GRAFI'; arg='--convertir'},
@{id='GRAFI_Abrir';name='Abrir con GRAFIPLOT PDF PRINT';arg=''}
)
foreach($it in $items){
 $key=[Microsoft.Win32.Registry]::CurrentUser.CreateSubKey('Software\Classes\*\shell\'+$it.id)
 $key.SetValue('',$it.name)
 $key.SetValue('Icon',(Join-Path $InstallDir 'GRAFIPLOT.ico'))
 $key.Close()
 $key=[Microsoft.Win32.Registry]::CurrentUser.CreateSubKey('Software\Classes\*\shell\'+$it.id+'\command')
 $cmd='"'+$python+'" "'+$app+'"'
 if($it.arg){$cmd+=' '+$it.arg}
 $cmd+=' "%1"'
 $key.SetValue('',$cmd)
 $key.Close()
 Write-Host ('ACTIVADO: '+$it.name)
}
