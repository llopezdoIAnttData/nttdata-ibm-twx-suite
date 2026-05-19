#!/usr/bin/env bash
# NTTDATA IBM TWX Reverse Engineering Suite v1.0.0
# Instalador para macOS y Linux
# Uso: chmod +x instalar_mac_linux.sh && ./instalar_mac_linux.sh

set -e

SUITE_VERSION="1.0.0"
CORP="NTTDATA"
REPO_URL="https://github.com/llopez2018/naves-industriales-ai.git"
BRANCH="claude/ibm-reverse-engineering-tools-8Arpa"

# Detectar OS y carpeta Documentos
if [[ "$OSTYPE" == "darwin"* ]]; then
  DOCS="$HOME/Documents"
  PYTHON="python3"
  PIP="pip3"
else
  DOCS="$HOME/Documentos"
  [[ ! -d "$DOCS" ]] && DOCS="$HOME/Documents"
  PYTHON="python3"
  PIP="pip3"
fi

DEST="$DOCS/NTTDATA-IBM-TWX-Suite"

# ── Banner ────────────────────────────────────────────────────────────────────
CYAN='\033[96m' GRN='\033[92m' YLW='\033[93m' RED='\033[91m' RST='\033[0m' DIM='\033[2m'

echo ""
echo -e "${CYAN}   ╭──────╮   ███╗  ██╗ ████████╗████████╗  ██████╗  █████╗ ████████╗ █████╗${RST}"
echo -e "${CYAN}  ╱ ╭────╮ ╲  ████╗ ██║ ╚══██╔══╝╚══██╔══╝  ██╔══██╗██╔══██╗╚══██╔══╝██╔══██╗${RST}"
echo -e "${CYAN} │  │  ◉  │ │ ██╔████╗██║    ██║      ██║   ██║  ██║███████║   ██║   ███████║${RST}"
echo -e "${CYAN} │  ╰────╯  │ ██║╚═██╗██║    ██║      ██║   ██║  ██║██╔══██║   ██║   ██╔══██║${RST}"
echo -e "${CYAN}  ╲         ╱  ██║  ╚████║    ██║      ██║   ██████╔╝██║  ██║   ██║   ██║  ██║${RST}"
echo -e "${CYAN}   ╰──────╯   ╚═╝   ╚═══╝    ╚═╝      ╚═╝   ╚═════╝ ╚═╝  ╚═╝   ╚═╝   ╚═╝  ╚═╝${RST}"
echo ""
echo -e "${DIM}  IBM TWX Reverse Engineering Suite  v${SUITE_VERSION}  |  Corporate: ${CORP}${RST}"
echo ""

# ── 1. Requisitos ─────────────────────────────────────────────────────────────
echo -e "${YLW}[1/5] Verificando requisitos...${RST}"
for cmd in $PYTHON git node npm; do
  if command -v $cmd &>/dev/null; then
    echo -e "  ${GRN}✓ $cmd$(${cmd} --version 2>&1 | head -1 | sed 's/^/ /')${RST}"
  else
    echo -e "  ${RED}✗ $cmd no encontrado — instálalo antes de continuar${RST}"
    exit 1
  fi
done

# ── 2. Crear carpetas ─────────────────────────────────────────────────────────
echo ""
echo -e "${YLW}[2/5] Creando estructura en Documentos...${RST}"
mkdir -p \
  "$DEST/01_herramientas_python/ibm_twx_tools" \
  "$DEST/02_extension_vscode/src" \
  "$DEST/02_extension_vscode/.vscode" \
  "$DEST/03_documentacion" \
  "$DEST/04_scripts" \
  "$DEST/05_muestras_twx"
echo -e "  ${GRN}✓ $DEST${RST}"

# ── 3. Clonar repo ────────────────────────────────────────────────────────────
echo ""
echo -e "${YLW}[3/5] Descargando suite desde GitHub...${RST}"
TMP=$(mktemp -d)
git clone --depth 1 --branch "$BRANCH" "$REPO_URL" "$TMP" -q
echo -e "  ${GRN}✓ Repositorio clonado${RST}"

# ── 4. Copiar archivos ────────────────────────────────────────────────────────
echo ""
echo -e "${YLW}[4/5] Organizando archivos...${RST}"

cp "$TMP"/ibm_twx_tools/*.py               "$DEST/01_herramientas_python/ibm_twx_tools/"
cp "$TMP"/setup.py                          "$DEST/01_herramientas_python/"
cp "$TMP"/vscode-nttdata-ibm/src/*.ts      "$DEST/02_extension_vscode/src/"
cp "$TMP"/vscode-nttdata-ibm/package.json  "$DEST/02_extension_vscode/"
cp "$TMP"/vscode-nttdata-ibm/tsconfig.json "$DEST/02_extension_vscode/"
cp "$TMP"/vscode-nttdata-ibm/.vscode/launch.json "$DEST/02_extension_vscode/.vscode/"
cp "$TMP"/NTTDATA-IBM-TWX-Suite/03_documentacion/* "$DEST/03_documentacion/"
cp "$TMP"/NTTDATA-IBM-TWX-Suite/04_scripts/*       "$DEST/04_scripts/"
cp "$TMP"/NTTDATA-IBM-TWX-Suite/index.html         "$DEST/"

chmod +x "$DEST/04_scripts/"*.sh
rm -rf "$TMP"
echo -e "  ${GRN}✓ Archivos organizados${RST}"

# ── 5. Instalar paquete Python ────────────────────────────────────────────────
echo ""
echo -e "${YLW}[5/5] Instalando paquete Python...${RST}"
cd "$DEST/01_herramientas_python"
$PIP install -e . -q --user
echo -e "  ${GRN}✓ nttdata-ibm-twx instalado${RST}"

# ── Resumen ───────────────────────────────────────────────────────────────────
echo ""
echo -e "${CYAN}══════════════════════════════════════════════════════${RST}"
echo -e "${GRN}  ✅  Instalación completada — NTTDATA IBM TWX Suite${RST}"
echo -e "${CYAN}══════════════════════════════════════════════════════${RST}"
echo ""
echo -e "  Carpeta:  ${CYAN}$DEST${RST}"
echo -e "  Comando:  ${CYAN}nttdata-ibm-twx --version${RST}"
echo -e "  Panel:    ${CYAN}$DEST/index.html${RST}  (abrir en navegador)"
echo ""
echo -e "  Prueba rápida:"
echo -e "    ${CYAN}nttdata-ibm-twx analyze tu_archivo.twx${RST}"
echo ""

# Abrir panel en navegador
read -rp "  ¿Abrir panel en el navegador ahora? (S/n): " OPEN
if [[ "${OPEN,,}" != "n" ]]; then
  if command -v open &>/dev/null; then open "$DEST/index.html"
  elif command -v xdg-open &>/dev/null; then xdg-open "$DEST/index.html"
  fi
fi
