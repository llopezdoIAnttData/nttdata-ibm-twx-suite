---
name: nttdata-update
description: >
  Updates and reinstalls all NTT DATA Copilot skills from the GitHub repository.
  Use this skill when the user types "/nttdata-update", "actualizar skills",
  "instalar skills", "update suite" or asks to refresh/reinstall the NTT DATA
  TWX skill suite. Pulls the latest version from GitHub and copies all skills
  and agents to ~/.copilot/.
allowed-tools: shell
---

# 🔄 NTT DATA — Update & Install Skills

Cuando este skill se activa, muestra el banner, ejecuta el script de
actualización y reporta el resultado.

---

## PASO 1 — Mostrar el banner de inicio

Imprime **exactamente** este bloque:

```
  ●
   ╭──────╮   ███╗  ██╗ ████████╗████████╗  ██████╗  █████╗ ████████╗ █████╗
  ╱ ╭────╮ ╲  ████╗ ██║ ╚══██╔══╝╚══██╔══╝  ██╔══██╗██╔══██╗╚══██╔══╝██╔══██╗
 │  │    │  │ ██╔████╗██║   ██║      ██║    ██║  ██║███████║   ██║   ███████║
 │  ╰────╯  │ ██║╚═██╗██║   ██║      ██║    ██║  ██║██╔══██║   ██║   ██╔══██║
  ╲         ╱  ██║  ╚████║   ██║      ██║    ██████╔╝██║  ██║   ██║   ██║  ██║
   ╰──────╯   ╚═╝   ╚═══╝   ╚═╝      ╚═╝    ╚═════╝ ╚═╝  ╚═╝   ╚═╝   ╚═╝  ╚═╝
  IBM TWX Reverse Engineering Suite  v1.1.0  ·  NTT DATA  ·  llopezdo@emeal.nttdata.com

  🔄  Actualizando skills desde GitHub...
```

---

## PASO 2 — Ejecutar el script de actualización

Ejecuta el siguiente bloque PowerShell **exactamente como está**,
usando la herramienta shell. No modifiques las rutas ni los comandos.

```powershell
$ErrorActionPreference = "Stop"
$REPO_URL  = "https://github.com/llopezdoIAnttData/nttdata-ibm-twx-suite.git"
$CACHE_DIR = "$env:USERPROFILE\.copilot\_suite_cache"
$SKILLS_DST = "$env:USERPROFILE\.copilot\skills"
$AGENTS_DST  = "$env:USERPROFILE\.copilot\agents"

Write-Host ""
Write-Host "  📦  Repo   : $REPO_URL"
Write-Host "  📂  Cache  : $CACHE_DIR"
Write-Host ""

# ── 1. Clone o Pull ────────────────────────────────────────────────────────────
if (Test-Path "$CACHE_DIR\.git") {
    Write-Host "  🔃  Actualizando repo existente..."
    Set-Location $CACHE_DIR
    git pull --ff-only origin master 2>&1 | ForEach-Object { "      $_" } | Write-Host
} else {
    Write-Host "  ⬇️   Clonando repo por primera vez..."
    if (Test-Path $CACHE_DIR) { Remove-Item $CACHE_DIR -Recurse -Force }
    git clone --depth=1 $REPO_URL $CACHE_DIR 2>&1 | ForEach-Object { "      $_" } | Write-Host
    Set-Location $CACHE_DIR
}

# ── 2. Crear destinos si no existen ───────────────────────────────────────────
New-Item -ItemType Directory -Force $SKILLS_DST | Out-Null
New-Item -ItemType Directory -Force $AGENTS_DST  | Out-Null

# ── 3. Copiar skills ──────────────────────────────────────────────────────────
$skillsSrc = Join-Path $CACHE_DIR ".copilot\skills"
$installed = @()
$updated   = @()

foreach ($skillDir in Get-ChildItem $skillsSrc -Directory) {
    $dst = Join-Path $SKILLS_DST $skillDir.Name
    $isNew = -not (Test-Path $dst)
    New-Item -ItemType Directory -Force $dst | Out-Null
    Get-ChildItem $skillDir.FullName | ForEach-Object {
        Copy-Item $_.FullName (Join-Path $dst $_.Name) -Force
    }
    if ($isNew) { $installed += $skillDir.Name }
    else        { $updated   += $skillDir.Name }
}

# ── 4. Copiar agentes ─────────────────────────────────────────────────────────
$agentsSrc = Join-Path $CACHE_DIR ".copilot\agents"
if (Test-Path $agentsSrc) {
    Get-ChildItem $agentsSrc -File | ForEach-Object {
        Copy-Item $_.FullName (Join-Path $AGENTS_DST $_.Name) -Force
    }
}

# ── 5. Mostrar resumen ────────────────────────────────────────────────────────
$total = $installed.Count + $updated.Count
Write-Host ""
Write-Host "  ✅  Instalación completada — $total skills"
Write-Host ""
if ($installed.Count -gt 0) {
    Write-Host "  🆕  NUEVOS ($($installed.Count)):"
    $installed | ForEach-Object { Write-Host "      + $_" }
    Write-Host ""
}
if ($updated.Count -gt 0) {
    Write-Host "  🔄  ACTUALIZADOS ($($updated.Count)):"
    $updated | ForEach-Object { Write-Host "      ↑ $_" }
    Write-Host ""
}
Write-Host "  📍  Skills en: $SKILLS_DST"
Write-Host "  📍  Agentes en: $AGENTS_DST"
Write-Host ""
Write-Host "  💡  Usa /skills reload en Copilot CLI para cargar los cambios."
Write-Host "      O simplemente reinicia tu sesión de Copilot."
Write-Host ""
```

---

## PASO 3 — Reportar resultado al usuario

Tras ejecutar el script, muestra al usuario:

- Cuántos skills se instalaron / actualizaron (usa los valores del resumen)
- La versión instalada (leer `CHANGELOG.md` del cache si es posible)
- Recordatorio: **reiniciar la sesión de Copilot** o ejecutar `/skills reload`
  para que los nuevos skills queden activos

Si el script falla, muestra el error exacto y sugiere:
1. Verificar que `git` esté instalado y en el PATH
2. Verificar conexión a internet / acceso a GitHub
3. Ejecutar manualmente: `git clone https://github.com/llopezdoIAnttData/nttdata-ibm-twx-suite.git`

---

## Notas
- El repo se guarda en `~/.copilot/_suite_cache/` para futuras actualizaciones rápidas (pull en vez de clone).
- El script es idempotente: se puede ejecutar N veces sin riesgo.
- Compatible con Windows (PowerShell 5.1+) y Linux/macOS (pwsh).
