$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$packageDir = Join-Path $root "qgis_package"
$zipPath = Join-Path $root "laubach_qgis_package.zip"

if (Test-Path $packageDir) {
    Remove-Item -Recurse -Force $packageDir
}
New-Item -ItemType Directory -Path $packageDir | Out-Null
New-Item -ItemType Directory -Path (Join-Path $packageDir "classification_outputs") | Out-Null

Copy-Item (Join-Path $root "laubach_feldwege.qgs") $packageDir -Force

Copy-Item (Join-Path $root "classification_outputs\laubach_feldwege_klassifiziert_linien.gpkg") (Join-Path $packageDir "classification_outputs") -Force
Copy-Item (Join-Path $root "classification_outputs\laubach_feldwege_klassifiziert_buffer.gpkg") (Join-Path $packageDir "classification_outputs") -Force
Copy-Item (Join-Path $root "classification_outputs\laubach_prediction_table.csv") (Join-Path $packageDir "classification_outputs") -Force
Copy-Item (Join-Path $root "classification_outputs\feldwege_klassifikation.sld") (Join-Path $packageDir "classification_outputs") -Force

if (Test-Path $zipPath) {
    Remove-Item $zipPath -Force
}
Compress-Archive -Path (Join-Path $packageDir "*") -DestinationPath $zipPath -Force

Write-Host "QGIS-Paket erstellt: $zipPath"
