# Script de instalacion para Windows (PowerShell)
# NTTDATA IBM TWX Reverse Engineering Suite v1.0.0
# Ejecutar desde PowerShell como administrador:
#   Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
#   .\instalar_windows.ps1

$ErrorActionPreference = "Stop"

$SUITE_VERSION = "1.0.0"
$CORP          = "NTTDATA"
$DEST          = Join-Path $env:USERPROFILE "Documents\NTTDATA-IBM-TWX-Suite"
$REPO_URL      = "https://github.com/llopez2018/naves-industriales-ai.git"
$BRANCH        = "claude/ibm-reverse-engineering-tools-8Arpa"

Write-Host ""
Write-Host "  ╭──────╮   ███╗  ██╗ ████████╗████████╗  ██████╗  █████╗ ████████╗ █████╗" -ForegroundColor Cyan
Write-Host "  ╱ ╭────╮ ╲  ████╗ ██║ ╚══██╔══╝╚══██╔══╝  ██╔══██╗██╔══██╗╚══██╔══╝██╔══██╗" -ForegroundColor Cyan
Write-Host " │  │  ◉  │ │ ██╔████╗██║    ██║      ██║   ██║  ██║███████║   ██║   ███████║" -ForegroundColor Cyan
Write-Host " │  ╰────╯  │ ██║╚═██╗██║    ██║      ██║   ██║  ██║██╔══██║   ██║   ██╔══██║" -ForegroundColor Cyan
Write-Host "  ╲         ╱  ██║  ╚████║    ██║      ██║   ██████╔╝██║  ██║   ██║   ██║  ██║" -ForegroundColor Cyan
Write-Host "   ╰──────╯   ╚═╝   ╚═══╝    ╚═╝      ╚═╝   ╚═════╝ ╚═╝  ╚═╝   ╚═╝   ╚═╝  ╚═╝" -ForegroundColor Cyan
Write-Host ""
Write-Host "  IBM TWX Reverse Engineering Suite  v$SUITE_VERSION  |  Corporate: $CORP" -ForegroundColor DarkCyan
Write-Host ""

# ── 1. Verificar requisitos ──────────────────────────────────────────────────
Write-Host "[1/5] Verificando requisitos..." -ForegroundColor Yellow

foreach ($cmd in @("python","git","node","npm")) {
    try {
        $null = & $cmd --version 2>&1
        Write-Host "  ✓ $cmd encontrado" -ForegroundColor Green
    } catch {
        Write-Host "  ✗ $cmd NO encontrado — instalalo antes de continuar" -ForegroundColor Red
        exit 1
    }
}

# ── 2. Crear carpeta en Documentos ──────────────────────────────────────────
Write-Host ""
Write-Host "[2/5] Creando estructura en Documentos..." -ForegroundColor Yellow

$folders = @(
    "$DEST",
    "$DEST\01_herramientas_python\ibm_twx_tools",
    "$DEST\02_extension_vscode\src",
    "$DEST\02_extension_vscode\.vscode",
    "$DEST\03_documentacion",
    "$DEST\04_scripts",
    "$DEST\05_muestras_twx"
)
foreach ($f in $folders) {
    New-Item -ItemType Directory -Force -Path $f | Out-Null
}
Write-Host "  ✓ Carpeta creada: $DEST" -ForegroundColor Green

# ── 3. Clonar / actualizar repo ──────────────────────────────────────────────
Write-Host ""
Write-Host "[3/5] Descargando suite desde GitHub..." -ForegroundColor Yellow

$TEMP = Join-Path $env:TEMP "nttdata_ibm_twx_tmp"
if (Test-Path $TEMP) { Remove-Item $TEMP -Recurse -Force }
git clone --depth 1 --branch $BRANCH $REPO_URL $TEMP
Write-Host "  ✓ Repositorio clonado" -ForegroundColor Green

# ── 4. Copiar archivos organizados ───────────────────────────────────────────
Write-Host ""
Write-Host "[4/5] Organizando archivos..." -ForegroundColor Yellow

# Python
Copy-Item "$TEMP\ibm_twx_tools\*.py"  "$DEST\01_herramientas_python\ibm_twx_tools\" -Force
Copy-Item "$TEMP\setup.py"            "$DEST\01_herramientas_python\"               -Force

# VS Code extension
Copy-Item "$TEMP\vscode-nttdata-ibm\src\*.ts"     "$DEST\02_extension_vscode\src\" -Force
Copy-Item "$TEMP\vscode-nttdata-ibm\package.json" "$DEST\02_extension_vscode\"     -Force
Copy-Item "$TEMP\vscode-nttdata-ibm\tsconfig.json""$DEST\02_extension_vscode\"     -Force
Copy-Item "$TEMP\vscode-nttdata-ibm\.vscode\launch.json" "$DEST\02_extension_vscode\.vscode\" -Force

# Docs
Copy-Item "$TEMP\NTTDATA-IBM-TWX-Suite\03_documentacion\*" "$DEST\03_documentacion\" -Force -Recurse
Copy-Item "$TEMP\NTTDATA-IBM-TWX-Suite\04_scripts\*"       "$DEST\04_scripts\"       -Force -Recurse
Copy-Item "$TEMP\NTTDATA-IBM-TWX-Suite\index.html"         "$DEST\"                  -Force

Write-Host "  ✓ Archivos organizados" -ForegroundColor Green

# ── 5. Instalar paquete Python ───────────────────────────────────────────────
Write-Host ""
Write-Host "[5/5] Instalando paquete Python..." -ForegroundColor Yellow

Push-Location "$DEST\01_herramientas_python"
python -m pip install -e . --quiet
Pop-Location

Write-Host "  ✓ nttdata-ibm-twx instalado en PATH" -ForegroundColor Green

# ── Limpiar temp ─────────────────────────────────────────────────────────────
Remove-Item $TEMP -Recurse -Force

# ── Resumen ───────────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "══════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  ✅  Instalacion completada — NTTDATA IBM TWX Suite" -ForegroundColor Green
Write-Host "══════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Carpeta:  $DEST" -ForegroundColor White
Write-Host "  Comando:  nttdata-ibm-twx --version" -ForegroundColor White
Write-Host "  Panel:    $DEST\index.html  (abrir en navegador)" -ForegroundColor White
Write-Host ""
Write-Host "  Prueba rapida:" -ForegroundColor DarkCyan
Write-Host "    nttdata-ibm-twx analyze tu_archivo.twx" -ForegroundColor Cyan
Write-Host ""

# Abrir el panel en el navegador
$indexPath = "$DEST\index.html"
if (Test-Path $indexPath) {
    $open = Read-Host "  ¿Abrir panel en el navegador ahora? (S/n)"
    if ($open -ne "n") { Start-Process $indexPath }
}
