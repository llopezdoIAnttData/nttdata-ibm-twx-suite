# ============================================================
#  NTTDATA IBM TWX Suite — Instalador desde GitHub
#  Uso:
#    Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
#    iwr https://raw.githubusercontent.com/llopezdoIAnttData/nttdata-ibm-twx-suite/master/04_scripts/instalar_windows.ps1 | iex
#  O localmente:
#    .\instalar_windows.ps1
# ============================================================

$ErrorActionPreference = "Stop"

# Forzar UTF-8 para caracteres del banner
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

$REPO_URL = "https://github.com/llopezdoIAnttData/nttdata-ibm-twx-suite.git"
$DEST     = Join-Path $env:USERPROFILE "Documents\NTTDATA-IBM-TWX-Suite"
$SKILLS   = Join-Path $env:USERPROFILE ".copilot\skills"
$AGENTS   = Join-Path $env:USERPROFILE ".copilot\agents"

# ── Banner ────────────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "  ██╗   ██╗████████╗████████╗    ██████╗  █████╗ ████████╗ █████╗ " -ForegroundColor Cyan
Write-Host "  ███╗  ██║╚══██╔══╝╚══██╔══╝    ██╔══██╗██╔══██╗╚══██╔══╝██╔══██╗" -ForegroundColor Cyan
Write-Host "  ██╔██╗██║   ██║      ██║       ██║  ██║███████║   ██║   ███████║" -ForegroundColor Cyan
Write-Host "  ██║╚████║   ██║      ██║       ██║  ██║██╔══██║   ██║   ██╔══██║" -ForegroundColor Cyan
Write-Host "  ██║ ╚███║   ██║      ██║       ██████╔╝██║  ██║   ██║   ██║  ██║" -ForegroundColor Cyan
Write-Host "  ╚═╝  ╚══╝   ╚═╝      ╚═╝       ╚═════╝ ╚═╝  ╚═╝   ╚═╝   ╚═╝  ╚═╝" -ForegroundColor Cyan
Write-Host ""
Write-Host "  IBM TWX Reverse Engineering Suite  v1.0.0" -ForegroundColor DarkCyan
Write-Host "  NTT DATA EMEAL · github.com/llopezdoIAnttData/nttdata-ibm-twx-suite" -ForegroundColor DarkGray
Write-Host ""

# ── 1. Requisitos ─────────────────────────────────────────────────────────────
Write-Host "[1/4] Verificando requisitos..." -ForegroundColor Yellow
$ok = $true
foreach ($cmd in @("python","git")) {
    try {
        $ver = & $cmd --version 2>&1
        Write-Host "  ✓ $cmd  ($ver)" -ForegroundColor Green
    } catch {
        Write-Host "  ✗ $cmd NO encontrado — instálalo y vuelve a ejecutar" -ForegroundColor Red
        $ok = $false
    }
}
if (-not $ok) { exit 1 }

# ── 2. Clonar o actualizar ────────────────────────────────────────────────────
Write-Host ""
Write-Host "[2/4] Descargando suite desde GitHub..." -ForegroundColor Yellow

if (Test-Path "$DEST\.git") {
    Write-Host "  → Repo ya existe, actualizando..." -ForegroundColor DarkCyan
    Push-Location $DEST
    git pull --quiet
    Pop-Location
    Write-Host "  ✓ Actualizado" -ForegroundColor Green
} else {
    if (Test-Path $DEST) { Remove-Item $DEST -Recurse -Force }
    git clone --depth 1 $REPO_URL $DEST
    Write-Host "  ✓ Clonado en: $DEST" -ForegroundColor Green
}

# ── 3. Instalar paquete Python ────────────────────────────────────────────────
Write-Host ""
Write-Host "[3/4] Instalando paquete Python (ibm_twx_tools)..." -ForegroundColor Yellow

Push-Location "$DEST\01_herramientas_python"
python -m pip install -e . --quiet
Pop-Location

# Verificar
try {
    $v = python -m ibm_twx_tools --version 2>&1
    Write-Host "  ✓ ibm_twx_tools instalado  ($v)" -ForegroundColor Green
} catch {
    Write-Host "  ✓ ibm_twx_tools instalado" -ForegroundColor Green
}

# ── 4. Instalar Copilot skills ────────────────────────────────────────────────
Write-Host ""
Write-Host "[4/4] Instalando skills de GitHub Copilot CLI..." -ForegroundColor Yellow

$skillsSrc = "$DEST\.copilot\skills"
$agentsSrc = "$DEST\.copilot\agents"

if (Test-Path $skillsSrc) {
    New-Item -ItemType Directory -Force -Path $SKILLS | Out-Null
    Copy-Item "$skillsSrc\*" $SKILLS -Recurse -Force
    Write-Host "  ✓ Skills copiados a: $SKILLS" -ForegroundColor Green
} else {
    Write-Host "  ℹ Skills no incluidos en repo — cópialos manualmente si los tienes en ~/.copilot/skills/" -ForegroundColor DarkYellow
}

if (Test-Path $agentsSrc) {
    New-Item -ItemType Directory -Force -Path $AGENTS | Out-Null
    Copy-Item "$agentsSrc\*" $AGENTS -Recurse -Force
    Write-Host "  ✓ Agentes copiados a: $AGENTS" -ForegroundColor Green
}

# ── Resumen ───────────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "══════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  ✅  Instalación completada" -ForegroundColor Green
Write-Host "══════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Carpeta  →  $DEST" -ForegroundColor White
Write-Host "  Análisis →  cd '$DEST'" -ForegroundColor White
Write-Host "             python run_analysis.py" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Verificar:" -ForegroundColor DarkCyan
Write-Host "    python -m ibm_twx_tools --help" -ForegroundColor Cyan
Write-Host ""

$open = Read-Host "  ¿Abrir panel index.html en el navegador ahora? (S/n)"
if ($open -ne "n") {
    Start-Process "$DEST\index.html"
}
