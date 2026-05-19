#!/usr/bin/env python3
"""
NTTDATA IBM TWX — Suite Agentica de Análisis v1.0.0
====================================================

Uso interactivo (recomendado):
    python run_analysis.py

Uso directo:
    python run_analysis.py <archivo.twx> [--output carpeta]

Genera en la carpeta de salida:
    01_analyze.json               Resumen de artefactos
    02_entities.json              Business Objects
    03_services.json              Servicios (IS / GSS / HHS)
    04_endpoints.json             Endpoints externos
    05_entries.json               Entry points
    06_flows.txt                  Diagramas Mermaid de flujos
    07_deps.txt                   Grafo de dependencias
    08_scripts.txt                Scripts JavaScript embebidos
    09_docs.md                    Documentación Markdown completa
    xml_extracts/                 XMLs clave extraídos del ZIP
    COPILOT_PROMPT.md             Prompt listo para Copilot (metodología v3)
    <nombre>_ExtraccionTecnica.html  ← Reporte HTML navegable completo
"""
    09_docs.md            Documentación Markdown completa
    xml_extracts/         XMLs clave extraídos del ZIP
    COPILOT_PROMPT.md     Prompt listo para Copilot (metodología v3)
"""

import argparse
import itertools
import json
import subprocess
import sys
import threading
import time
import zipfile
from datetime import datetime
from pathlib import Path

# ── Colores ANSI ──────────────────────────────────────────────────────────────
_RS  = "\033[0m"
_BD  = "\033[1m"
_DM  = "\033[2m"
_B   = "\033[38;5;27m"   # NTT DATA bright blue
_LB  = "\033[38;5;81m"   # light blue
_G   = "\033[38;5;40m"   # green  ✓
_Y   = "\033[38;5;214m"  # amber  ⚠
_R   = "\033[38;5;196m"  # red    ✗
_S   = "\033[38;5;252m"  # silver
_T   = "\033[38;5;43m"   # teal

def _ok(msg):   print(f"    {_G}✓{_RS}  {msg}")
def _warn(msg): print(f"    {_Y}⚠{_RS}  {msg}")
def _err(msg):  print(f"    {_R}✗{_RS}  {msg}")
def _hdr(msg):  print(f"\n  {_B}{_BD}▸{_RS} {_BD}{msg}{_RS}")
def _sub(msg):  print(f"    {_S}{msg}{_RS}")


# ── Spinner animado ────────────────────────────────────────────────────────────

class Spinner:
    """Spinner inline que se limpia al terminar."""
    FRAMES = ["⠋","⠙","⠹","⠸","⠼","⠴","⠦","⠧","⠇","⠏"]

    def __init__(self, label: str):
        self.label  = label
        self._stop  = threading.Event()
        self._thread = threading.Thread(target=self._spin, daemon=True)

    def _spin(self):
        for frame in itertools.cycle(self.FRAMES):
            if self._stop.is_set():
                break
            print(f"\r    {_B}{frame}{_RS}  {self.label}...", end="", flush=True)
            time.sleep(0.08)

    def __enter__(self):
        self._thread.start()
        return self

    def __exit__(self, *_):
        self._stop.set()
        self._thread.join()
        print("\r" + " " * (len(self.label) + 12) + "\r", end="", flush=True)


# ── Rutas ─────────────────────────────────────────────────────────────────────
SCRIPT_DIR   = Path(__file__).parent
TOOLS_DIR    = SCRIPT_DIR / "01_herramientas_python"
PYTHON       = sys.executable


# ── Helpers ───────────────────────────────────────────────────────────────────

def run_command(command: str, twx_path: Path, output_file: Path, extra_args: list = None,
                agent_label: str = ""):
    """Ejecuta un comando de ibm_twx_tools y guarda el output."""
    cmd = [PYTHON, "-m", "ibm_twx_tools", command, str(twx_path)]
    if extra_args:
        cmd.extend(extra_args)

    label = agent_label or command
    with Spinner(label):
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                cwd=str(TOOLS_DIR),
            )
        except Exception as exc:
            _err(f"{command}: {exc}")
            return False

    if result.returncode != 0:
        _err(f"{label}: {result.stderr.strip()[:120]}")
        return False

    output_file.write_text(result.stdout, encoding="utf-8")
    size_kb = output_file.stat().st_size / 1024
    _ok(f"{label:40s} {_DM}→ {output_file.name}  ({size_kb:.1f} KB){_RS}")
    return True


def extract_xml_artifacts(twx_path: Path, xml_dir: Path):
    """Extrae los XMLs clave del TWX (ZIP) a subcarpetas por prefijo."""
    xml_dir.mkdir(parents=True, exist_ok=True)

    prefix_map = {
        "manifest": xml_dir,          # manifest.xml → raíz
        "1.":  xml_dir / "01_services",
        "4.":  xml_dir / "04_ucas",
        "12.": xml_dir / "12_business_objects",
        "25.": xml_dir / "25_bpds",
        "64.": xml_dir / "64_coach_views",
    }

    # Crear subcarpetas
    for path in prefix_map.values():
        if isinstance(path, Path):
            path.mkdir(parents=True, exist_ok=True)

    counts = {k: 0 for k in prefix_map}

    try:
        with zipfile.ZipFile(twx_path, "r") as zf:
            for name in zf.namelist():
                filename = Path(name).name

                # manifest.xml
                if filename == "manifest.xml":
                    dest = prefix_map["manifest"] / "manifest.xml"
                    dest.write_bytes(zf.read(name))
                    counts["manifest"] += 1
                    continue

                # XMLs por prefijo numérico
                for prefix, dest_dir in prefix_map.items():
                    if prefix == "manifest":
                        continue
                    if filename.startswith(prefix) and filename.endswith(".xml"):
                        dest = dest_dir / filename
                        dest.write_bytes(zf.read(name))
                        counts[prefix] += 1
                        break

    except (zipfile.BadZipFile, Exception) as exc:
        _err(f"Error extrayendo XMLs: {exc}")
        return counts

    _ok(f"manifest.xml")
    for prefix, label, subdir in [
        ("1.",  "01_services      ", "01_services"),
        ("4.",  "04_ucas          ", "04_ucas"),
        ("12.", "12_business_obj  ", "12_business_objects"),
        ("25.", "25_bpds          ", "25_bpds"),
        ("64.", "64_coach_views   ", "64_coach_views"),
    ]:
        n = counts.get(prefix, 0)
        _ok(f"{label} {_DM}→ {n:3d} archivos{_RS}")
    return counts


def load_json(path: Path) -> str:
    """Carga un JSON y retorna primeros N caracteres para el prompt."""
    try:
        text = path.read_text(encoding="utf-8")
        data = json.loads(text)
        # Truncar para no exceder contexto en el prompt
        if isinstance(data, list) and len(text) > 20_000:
            return json.dumps(data[:30], indent=2, ensure_ascii=False) + f"\n... ({len(data)} items total)"
        return text[:25_000] + ("..." if len(text) > 25_000 else "")
    except Exception:
        return "(no disponible)"


def load_text(path: Path, max_chars: int = 15_000) -> str:
    try:
        text = path.read_text(encoding="utf-8")
        return text[:max_chars] + ("..." if len(text) > max_chars else "")
    except Exception:
        return "(no disponible)"


def load_xml_list(xml_dir: Path, subdir: str) -> str:
    """Lista los archivos XML en un subdirectorio."""
    target = xml_dir / subdir
    if not target.exists():
        return "(directorio no encontrado)"
    files = sorted(target.glob("*.xml"))
    if not files:
        return "(sin archivos)"
    return "\n".join(f"  - {f.name}" for f in files)


def generate_copilot_prompt(
    twx_name: str,
    out_dir: Path,
    xml_dir: Path,
    analyze_json: str,
    entities_json: str,
    services_json: str,
    endpoints_json: str,
    flows_txt: str,
    scripts_txt: str,
) -> str:
    """Genera el prompt maestro para Copilot con metodología v3."""

    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    coach_views_list = load_xml_list(xml_dir, "64_coach_views")
    ucas_list        = load_xml_list(xml_dir, "04_ucas")
    bpds_list        = load_xml_list(xml_dir, "25_bpds")
    services_list    = load_xml_list(xml_dir, "01_services")

    manifest_path = xml_dir / "manifest.xml"
    manifest_content = load_text(manifest_path, 8_000) if manifest_path.exists() else "(no encontrado)"

    return f"""<!--
  NTTDATA IBM TWX — Prompt Maestro para Copilot
  Archivo TWX : {twx_name}
  Generado    : {now}
  Metodología : Extracción Técnica v3
  Skill       : profuturo-twx
-->

# Análisis completo de `{twx_name}` — Metodología v3

> **Instrucción para Copilot:**
> Aplica el skill `profuturo-twx` y ejecuta los **8 ciclos de extracción v3** usando
> los datos pre-extraídos en este documento. Genera las 10 secciones de la
> Arquitectura de Conocimiento con el formato establecido en el HTML de referencia.
>
> Los XMLs clave se encuentran en: `{xml_dir}`

---

## DATOS PRE-EXTRAÍDOS

### CICLO 1 — Estructura del TWX (`analyze`)

```json
{analyze_json}
```

---

### CICLO 2 — Constantes de entorno (`manifest.xml`)

Archivo: `{manifest_path}`

```xml
{manifest_content}
```

---

### CICLO 3 — Integration Services (ciclo `services`)

Servicios disponibles en `{xml_dir / "01_services"}`:
{services_list}

Datos extraídos:
```json
{services_json[:15_000]}{"..." if len(services_json) > 15_000 else ""}
```

---

### CICLO 4 — Coach Views / Botones HHS (prefijo `64.*`)

Archivos en `{xml_dir / "64_coach_views"}`:
{coach_views_list}

> **REGLA CRÍTICA v3:** Los botones de cada HHS viven en los archivos `64.*.xml`,
> NO en las descripciones de los HHS. Leer cada `<boundaryEvent>` y `<postponeAction>`.
> `PostponeAction` = "Cerrar tarea en Appian" (NO Posponer, NO Cancelar).

**Tarea:** Para cada archivo `64.*`, extraer:
- Nombre del Coach View (= nombre del HHS asociado)
- Cada `<boundaryEvent>` → nombre del botón + condición
- `<postponeAction>` → "Cerrar tarea en Appian"
- `tw.options.nombreBoton` → botón dinámico (implementar con expresión en Appian)

---

### CICLO 5 — UCAs con correlación de datos (prefijo `4.*`)

Archivos en `{xml_dir / "04_ucas"}`:
{ucas_list}

Endpoints externos:
```json
{endpoints_json[:8_000]}{"..." if len(endpoints_json) > 8_000 else ""}
```

> **Tarea:** Para cada UCA extraer: `schedEvent` (cola BUS que lo activa),
> `linkedService`, BPD donde reanuda, correlación de campos BUS → `tw.local.*`,
> gateway de decisión inmediatamente posterior.

---

### CICLO 6 — GSS en orden real por sequenceFlow

> **REGLA CRÍTICA v3:** Construir grafo siguiendo `<sequenceFlow>` desde `startEvent`
> hasta `ExitPoint`. NUNCA usar orden de aparición en XML ni coordenadas X/Y.

Flujos extraídos (Mermaid):
```
{flows_txt[:12_000]}{"..." if len(flows_txt) > 12_000 else ""}
```

---

### CICLO 7 — Tabla de decisiones (gateways en BPDs `25.*`)

BPDs disponibles en `{xml_dir / "25_bpds"}`:
{bpds_list}

Scripts embebidos (condiciones JS):
```
{scripts_txt[:12_000]}{"..." if len(scripts_txt) > 12_000 else ""}
```

> **Tarea:** Para cada `<exclusiveGateway>` en los BPDs, extraer:
> - Nombre del gateway
> - Variable de decisión (`tw.local.salida`, `tw.local.exitoso`, etc.)
> - Condiciones de cada rama de salida
> - Destino de cada rama

---

### CICLO 8 — Mapeo BUS/MQ → NOV_INSTANCE_MANAGEMENT

> **Patrón IBM:** IS → BUS message → IIB → GSS Respuesta → InvokeUCA → BPD reanuda
>
> **Patrón Appian (NOV_INSTANCE_MANAGEMENT):**
> - INSERT al llamar el IS
> - UPDATE IS_ACTIVE=0 cuando IIB responde
> - El proceso Appian reacciona al cambio de `STATUS_ID`
>
> Mapeo: `tw.local.salida` → `ACTION_OUT` | `tw.local.exitoso` → `STATUS_ID` |
> `tw.local.mensaje` → `RESPONSE_OUT`
>
> **Tarea:** Cruzar los UCAs identificados en Ciclo 5 con el esquema
> `NOV_INSTANCE_MANAGEMENT` y documentar el flujo completo campo a campo.

---

### Business Objects / Entidades

```json
{entities_json[:10_000]}{"..." if len(entities_json) > 10_000 else ""}
```

---

## INSTRUCCIONES DE SALIDA

Genera las siguientes **10 secciones** con el mismo formato del documento de referencia
`ArquitecturaConocimiento_v1.html`:

| Sección | Contenido |
|---------|-----------|
| **Sección 1** | Constantes de entorno — 71 variables por categoría y ambiente |
| **Sección 2** | Endpoints IS — nombre, operación WSDL, URL patrón |
| **Sección 3** | Payloads — campos INPUT/OUTPUT por IS con tipos `tw.local.*` |
| **Sección 4** | Botones HHS — 105 botones de 21 HHS desde los `64.*` |
| **Sección 5** | Business Objects — estructura de datos y herencia |
| **Sección 6** | Tabla de decisiones — gateways + condiciones + scripts |
| **Sección 7** | UCAs — correlación BUS→process completa |
| **Sección 8** | GSS — pasos en orden real por sequenceFlow |
| **Sección 9** | BPDs — estructura de procesos y subprocesos |
| **Sección 10** | Mapeo BUS/MQ — campo a campo + flujo Appian documentado |

---

*Generado por NTTDATA IBM TWX Run Analysis v1.0.0 — {now}*
"""


# ── Banner ────────────────────────────────────────────────────────────────────

def show_banner():
    w = 62
    bar = f"{_B}{_BD}{'═' * w}{_RS}"
    print(f"\n{bar}")
    print(f"  {_LB}{_BD}  ██╗   ██╗████████╗████████╗    ██████╗  █████╗ ████████╗ █████╗ {_RS}")
    print(f"  {_LB}{_BD}  ███╗  ██║╚══██╔══╝╚══██╔══╝    ██╔══██╗██╔══██╗╚══██╔══╝██╔══██╗{_RS}")
    print(f"  {_LB}{_BD}  ██╔██╗██║   ██║      ██║       ██║  ██║███████║   ██║   ███████║{_RS}")
    print(f"  {_LB}{_BD}  ██║╚████║   ██║      ██║       ██║  ██║██╔══██║   ██║   ██╔══██║{_RS}")
    print(f"  {_LB}{_BD}  ██║ ╚███║   ██║      ██║       ██████╔╝██║  ██║   ██║   ██║  ██║{_RS}")
    print(f"  {_LB}{_BD}  ╚═╝  ╚══╝   ╚═╝      ╚═╝       ╚═════╝ ╚═╝  ╚═╝   ╚═╝   ╚═╝  ╚═╝{_RS}")
    print(f"{bar}")
    print(f"  {_B}IBM TWX Reverse Engineering Suite{_RS}  {_S}v1.0.0{_RS}")
    print(f"  {_S}NTT DATA EMEAL · Migración IBM BPM → Appian{_RS}")
    print(f"{bar}\n")


# ── Prompt interactivo ────────────────────────────────────────────────────────

def ask_twx_path() -> Path:
    """Solicita al usuario la ruta del archivo .TWX de forma interactiva."""
    print(f"  {_B}▸{_RS} {_BD}Agente de Extracción TWX listo{_RS}")
    print(f"  {_S}Este proceso ejecutará 9 ciclos de análisis + extracción XML{_RS}")
    print(f"  {_S}y generará el prompt optimizado para Copilot con metodología v3.{_RS}\n")

    while True:
        try:
            raw = input(f"  {_B}📁{_RS} {_BD}Ruta del archivo .TWX:{_RS} ").strip()
        except (EOFError, KeyboardInterrupt):
            print(f"\n  {_Y}Cancelado.{_RS}\n")
            sys.exit(0)

        if not raw:
            _warn("Por favor ingresa la ruta del archivo.")
            continue

        # Quitar comillas si las pegaron con comillas
        raw = raw.strip('"').strip("'")
        path = Path(raw)
        if not path.is_absolute():
            path = Path.cwd() / path
        path = path.resolve()

        if not path.exists():
            _err(f"No se encontró: {path}")
            continue
        if path.suffix.lower() != ".twx":
            _warn(f"La extensión no es .twx ({path.suffix}). ¿Continuar? [s/N] ")
            ans = input("  ").strip().lower()
            if ans not in ("s", "si", "sí", "y", "yes"):
                continue
        return path


# ── Cabecera de fase ───────────────────────────────────────────────────────────

def phase_header(n: int, title: str, agent: str):
    pad = 56
    print(f"\n  {_B}{_BD}{'─'*pad}{_RS}")
    print(f"  {_B}{_BD}  FASE {n}  {_RS}{_BD}{title}{_RS}")
    print(f"  {_S}  sub-agente: {_T}{agent}{_RS}")
    print(f"  {_B}{_BD}{'─'*pad}{_RS}\n")


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="NTTDATA IBM TWX — Suite Agentica de Análisis",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        add_help=True,
    )
    parser.add_argument("twx_file", nargs="?", default=None,
                        help="Ruta al archivo .twx  (opcional — se pregunta si se omite)")
    parser.add_argument("--output", "-o", default=None,
                        help="Carpeta de salida  (default: ./output/<nombre_twx>/)")
    args = parser.parse_args()

    show_banner()

    # ── Resolución de ruta ────────────────────────────────────────────────────
    if args.twx_file:
        twx_path = Path(args.twx_file).resolve()
        if not twx_path.exists():
            _err(f"Archivo no encontrado: {twx_path}")
            sys.exit(1)
        if twx_path.suffix.lower() != ".twx":
            _warn(f"La extensión no es .twx: {twx_path.name}")
    else:
        twx_path = ask_twx_path()

    twx_name = twx_path.stem
    out_dir  = Path(args.output).resolve() if args.output else SCRIPT_DIR / "output" / twx_name
    out_dir.mkdir(parents=True, exist_ok=True)
    xml_dir  = out_dir / "xml_extracts"

    print(f"\n  {_S}TWX    :{_RS} {_BD}{twx_path.name}{_RS}")
    print(f"  {_S}Salida :{_RS} {out_dir}")
    print(f"  {_S}Inicio :{_RS} {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # ── FASE 1: Ciclos de análisis Python ─────────────────────────────────────
    phase_header(1, "Extracción automática — 9 Ciclos", "twx-suite / ciclos 1-9")

    commands = [
        ("analyze",   "01_analyze.json",   [],  "Ciclo 1 · Resumen de artefactos    [twx-analyze]"),
        ("entities",  "02_entities.json",  [],  "Ciclo 2 · Business Objects         [twx-entities]"),
        ("services",  "03_services.json",  [],  "Ciclo 3 · Servicios IS/GSS/HHS     [twx-services]"),
        ("endpoints", "04_endpoints.json", [],  "Ciclo 4 · Endpoints externos        [twx-endpoints]"),
        ("entries",   "05_entries.json",   [],  "Ciclo 5 · Entry points / UCAs       [twx-entries]"),
        ("flows",     "06_flows.txt",      [],  "Ciclo 6 · Flujos Mermaid            [twx-flows]"),
        ("deps",      "07_deps.txt",       [],  "Ciclo 7 · Grafo dependencias        [twx-deps]"),
        ("scripts",   "08_scripts.txt",    [],  "Ciclo 8 · Scripts embebidos         [twx-scripts]"),
        ("docs",      "09_docs.md",        [],  "Ciclo 9 · Documentación Markdown    [twx-docs]"),
    ]

    results = {}
    for cmd, filename, extra, agent_label in commands:
        output_file = out_dir / filename
        ok = run_command(cmd, twx_path, output_file, extra, agent_label)
        results[cmd] = output_file if ok else None

    # ── FASE 2: Extracción de XMLs ────────────────────────────────────────────
    phase_header(2, "Extracción de XMLs del archivo ZIP", "twx-xml-extractor")
    xml_counts = extract_xml_artifacts(twx_path, xml_dir)

    # ── FASE 3: Generación del prompt Copilot ─────────────────────────────────
    phase_header(3, "Generando COPILOT_PROMPT.md — Metodología v3", "profuturo-twx / twx-engineer")

    def safe_load_json(key):
        f = results.get(key)
        return load_json(f) if f and f.exists() else "(no disponible)"

    def safe_load_text(key):
        f = results.get(key)
        return load_text(f) if f and f.exists() else "(no disponible)"

    with Spinner("Construyendo prompt v3 con reglas de metodología"):
        prompt = generate_copilot_prompt(
            twx_name       = twx_path.name,
            out_dir        = out_dir,
            xml_dir        = xml_dir,
            analyze_json   = safe_load_json("analyze"),
            entities_json  = safe_load_json("entities"),
            services_json  = safe_load_json("services"),
            endpoints_json = safe_load_json("endpoints"),
            flows_txt      = safe_load_text("flows"),
            scripts_txt    = safe_load_text("scripts"),
        )

    prompt_file = out_dir / "COPILOT_PROMPT.md"
    prompt_file.write_text(prompt, encoding="utf-8")
    size_kb = prompt_file.stat().st_size / 1024
    _ok(f"{'COPILOT_PROMPT.md generado':40s} {_DM}({size_kb:.1f} KB){_RS}")

    # ── FASE 4: Generar reporte HTML navegable ────────────────────────────────
    phase_header(4, "Generando reporte HTML navegable", "html-report-generator")

    try:
        sys.path.insert(0, str(TOOLS_DIR))
        from ibm_twx_tools.html_report import generate_report
        with Spinner("Construyendo HTML con 9 secciones técnicas"):
            report_path = generate_report(out_dir, twx_name)
        size_kb_html = report_path.stat().st_size / 1024
        _ok(f"{report_path.name:40s} {_DM}({size_kb_html:.1f} KB){_RS}")
    except Exception as exc:
        _warn(f"HTML no generado: {exc}")
        report_path = None

    # ── Resumen final ─────────────────────────────────────────────────────────
    successful = sum(1 for v in results.values() if v and v.exists())
    total      = len(commands)

    print(f"\n  {_B}{_BD}{'═' * 62}{_RS}")
    print(f"  {_G}{_BD}  ✓  Análisis completado{_RS}")
    print(f"  {_S}     Ciclos ejecutados : {_RS}{_BD}{successful}/{total}{_RS}")
    print(f"  {_S}     XMLs extraídos    : {_RS}{_BD}{sum(xml_counts.values())}{_RS}")
    print(f"  {_S}     Carpeta de salida : {_RS}{out_dir}")
    if report_path and report_path.exists():
        print(f"  {_G}     Reporte HTML      : {_RS}{_BD}{report_path.name}{_RS}")
    print(f"  {_B}{_BD}{'═' * 62}{_RS}\n")
    print(f"  {_Y}{_BD}▸  Siguiente paso:{_RS}")
    if report_path and report_path.exists():
        print(f"     → Abre el reporte HTML: {_BD}{report_path}{_RS}")
    print(f"     → O usa {_B}{_BD}profuturo-twx{_RS} con el COPILOT_PROMPT.md para análisis profundo\n")


if __name__ == "__main__":
    main()
