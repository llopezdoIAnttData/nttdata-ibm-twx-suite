#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════╗
║         NTT DATA — IBM BPM → Appian · Pipeline Orchestrator             ║
║         Sistema Multi-Agente de Análisis Profundo                       ║
╚══════════════════════════════════════════════════════════════════════════╝

Agentes del sistema:
  Agent-1 · Discovery      : Inventario de todos los TWX y sus artefactos
  Agent-2 · Entities       : Extracción y clasificación de Business Objects
  Agent-3 · Services       : Extracción de IS/HHS/GSS con pasos y lógica
  Agent-4 · IS-Parameters  : WebServices SOAP con params REQUEST/RESPONSE
  Agent-5 · BPD-Variables  : Variables de proceso + mapeo NCI_BR
  Agent-6 · Cross-Model    : BOs compartidos entre módulos (toolkit candidates)
  Agent-7 · Parametria-F3  : Arquitectura F3, async Tipo 2, NOV_INSTANCE_MANAGEMENT
  Agent-8 · Appian-Generator: Genera paquetes Appian importables por módulo
  Agent-9 · Report         : HTML maestro con resultados de todos los agentes

Uso:
  python pipeline_orchestrator.py --dir "<ruta_directorio_twx>"
  python pipeline_orchestrator.py --dir "<ruta>" --output "<ruta_salida>"
  python pipeline_orchestrator.py --dir "<ruta>" --prefix NCI_RB --agents 1,2,3,4
  python pipeline_orchestrator.py --dir "<ruta>" --only is-params
"""

import argparse
import glob
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

# ── Ensure UTF-8 output on Windows ───────────────────────────────────────────
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# ── Constants ────────────────────────────────────────────────────────────────
VERSION    = "1.0.0"
CORPORATE  = "NTT DATA"
TOOL_CMD   = [sys.executable, "-m", "ibm_twx_tools"]
GEN_CMD    = [sys.executable, "-m", "appian_generator.ibm_to_appian_pipeline"]

# ── Color codes (Windows-compatible) ────────────────────────────────────────
R  = "\033[91m"   # red
G  = "\033[92m"   # green
Y  = "\033[93m"   # yellow
B  = "\033[94m"   # blue
M  = "\033[95m"   # magenta
C  = "\033[96m"   # cyan
W  = "\033[97m"   # white
DIM= "\033[2m"
RESET = "\033[0m"


def banner():
    print(f"""
{R}╔══════════════════════════════════════════════════════════════════════════╗{RESET}
{R}║{RESET}  {W}{CORPORATE}{RESET}  ·  IBM BPM → Appian  ·  Pipeline Orquestador Multi-Agente        {R}║{RESET}
{R}║{RESET}  {DIM}Sistema de Análisis Profundo v{VERSION}  ·  9 Agentes Especializados{RESET}        {R}║{RESET}
{R}╚══════════════════════════════════════════════════════════════════════════╝{RESET}
""")


def step(agent_id: int, name: str, desc: str):
    print(f"\n{B}{'─'*72}{RESET}")
    print(f"{B}  Agent-{agent_id}{RESET} · {W}{name}{RESET}")
    print(f"  {DIM}{desc}{RESET}")
    print(f"{B}{'─'*72}{RESET}")


def ok(msg: str):    print(f"  {G}✓{RESET}  {msg}")
def warn(msg: str):  print(f"  {Y}⚠{RESET}  {msg}", file=sys.stderr)
def err(msg: str):   print(f"  {R}✗{RESET}  {msg}", file=sys.stderr)
def info(msg: str):  print(f"  {C}·{RESET}  {DIM}{msg}{RESET}")


def run_tool(cmd_args: list, capture: bool = True) -> tuple[bool, str]:
    """Run a sub-command and return (success, output)."""
    try:
        result = subprocess.run(
            cmd_args,
            capture_output=capture,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=300,
        )
        if result.returncode != 0 and result.stderr:
            return False, result.stderr.strip()
        return True, (result.stdout or "")
    except subprocess.TimeoutExpired:
        return False, "Timeout (300s)"
    except Exception as exc:
        return False, str(exc)


def derive_module_name(twx_path: str) -> str:
    """'Profuturo_Redencion_Bono_AP - 1.17.48.twx' → 'Redencion Bono'"""
    stem = Path(twx_path).stem
    mod  = stem.split(" - ")[0]
    mod  = re.sub(r"^Profuturo_", "", mod)
    mod  = mod.replace("_AP", "").replace("_", " ").strip()
    return mod


# ════════════════════════════════════════════════════════════════════════════
# AGENT 1 — Discovery
# ════════════════════════════════════════════════════════════════════════════

def agent_discovery(twx_files: list[str], out_dir: Path) -> dict:
    step(1, "Discovery", "Inventario completo de artefactos en todos los TWX")

    inventory = {"modules": [], "total": {}}
    total_counts: dict[str, int] = {}

    for twx in twx_files:
        mod = derive_module_name(twx)
        info(f"Analizando: {mod}")
        ok_flag, output = run_tool(TOOL_CMD + ["analyze", twx])
        if ok_flag:
            try:
                data = json.loads(output)
                counts = data.get("by_type", {})
                for k, v in counts.items():
                    total_counts[k] = total_counts.get(k, 0) + v
                module_entry = {
                    "name": mod,
                    "file": os.path.basename(twx),
                    "app_name": data.get("app_name", mod),
                    "version": data.get("app_version", ""),
                    "total_artifacts": data.get("total_artifacts", 0),
                    "by_type": counts,
                }
                inventory["modules"].append(module_entry)
                ok(f"{mod}: {data.get('total_artifacts',0)} artefactos")
            except json.JSONDecodeError:
                warn(f"{mod}: no se pudo parsear JSON del analyze")
        else:
            warn(f"{mod}: {output[:80]}")

    inventory["total"] = total_counts
    inventory["module_count"] = len(inventory["modules"])

    out_path = out_dir / "agent1_discovery.json"
    out_path.write_text(json.dumps(inventory, indent=2, ensure_ascii=False), encoding="utf-8")
    ok(f"Discovery completo: {len(twx_files)} módulos → {out_path.name}")
    return inventory


# ════════════════════════════════════════════════════════════════════════════
# AGENT 2 — Entities (Business Objects)
# ════════════════════════════════════════════════════════════════════════════

def agent_entities(twx_files: list[str], out_dir: Path) -> dict:
    step(2, "Entities", "Extracción y clasificación de Business Objects por módulo")

    result = {"modules": {}, "all_bos": [], "classification": {"domain_entity": [], "dto": [], "catalog": []}}
    all_names: set[str] = set()

    for twx in twx_files:
        mod = derive_module_name(twx)
        ok_flag, output = run_tool(TOOL_CMD + ["entities", twx])
        if ok_flag:
            try:
                bos = json.loads(output)
                result["modules"][mod] = bos
                for bo in bos:
                    name = bo.get("name", "")
                    if name not in all_names:
                        all_names.add(name)
                        bo["_module"] = mod
                        result["all_bos"].append(bo)
                ok(f"{mod}: {len(bos)} BOs")
            except json.JSONDecodeError:
                warn(f"{mod}: JSON parse error en entities")

    # Classify by name heuristics
    catalog_kw = {"catalogo","catalog","tipo","estatus","status","siefore","subcuenta","origen","regimen","grupo","banco"}
    domain_kw  = {"folio","identificador","idarchivo","foliosubsecuente"}

    for bo in result["all_bos"]:
        name_l = bo.get("name","").lower()
        fields = {f.get("name","").lower() for f in bo.get("fields", [])}
        n_fields = len(bo.get("fields", []))
        if any(kw in name_l for kw in catalog_kw):
            cat = "catalog"
        elif fields & domain_kw or n_fields > 10:
            cat = "domain_entity"
        else:
            cat = "dto"
        bo["_category"] = cat
        result["classification"][cat].append(bo.get("name",""))

    out_path = out_dir / "agent2_entities.json"
    out_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    total_bos = len(result["all_bos"])
    ok(f"Entities completo: {total_bos} BOs únicos · domain_entity={len(result['classification']['domain_entity'])} · dto={len(result['classification']['dto'])} · catalog={len(result['classification']['catalog'])}")
    return result


# ════════════════════════════════════════════════════════════════════════════
# AGENT 3 — Services
# ════════════════════════════════════════════════════════════════════════════

def agent_services(twx_files: list[str], out_dir: Path) -> dict:
    step(3, "Services", "Extracción de IS/HHS/GSS con pasos, inputs/outputs y lógica")

    result = {"modules": {}, "totals": {"is": 0, "hhs": 0, "gss": 0, "total": 0}}

    for twx in twx_files:
        mod = derive_module_name(twx)
        ok_flag, output = run_tool(TOOL_CMD + ["services", twx])
        if ok_flag:
            try:
                services = json.loads(output)
                result["modules"][mod] = services
                counts = {"is": 0, "hhs": 0, "gss": 0}
                for svc in services:
                    t = svc.get("service_type","").lower()
                    if "is" in t or "integration" in t: counts["is"] += 1
                    elif "hhs" in t or "human" in t:    counts["hhs"] += 1
                    elif "gss" in t or "general" in t:  counts["gss"] += 1
                for k in counts:
                    result["totals"][k] += counts[k]
                result["totals"]["total"] += len(services)
                ok(f"{mod}: {len(services)} services (IS={counts['is']}, HHS={counts['hhs']}, GSS={counts['gss']})")
            except json.JSONDecodeError:
                warn(f"{mod}: JSON parse error en services")

    out_path = out_dir / "agent3_services.json"
    out_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    ok(f"Services completo: {result['totals']['total']} total · IS={result['totals']['is']} · HHS={result['totals']['hhs']} · GSS={result['totals']['gss']}")
    return result


# ════════════════════════════════════════════════════════════════════════════
# AGENT 4 — IS Parameters (SOAP WebServices)
# ════════════════════════════════════════════════════════════════════════════

def agent_is_params(twx_dir: str, out_dir: Path) -> dict:
    step(4, "IS-Parameters", "WebServices SOAP: operaciones REQUEST/RESPONSE + detección Async Tipo 2")

    html_path = out_dir / "is_parameters_report.html"
    ok_flag, output = run_tool(
        TOOL_CMD + ["is-params", "--dir", twx_dir, "-o", str(html_path)],
        capture=False,
    )

    result = {"html_report": str(html_path), "generated": ok_flag}

    if ok_flag:
        ok(f"Reporte IS generado: {html_path.name}")
    else:
        warn(f"is-params completó con avisos — revisar {html_path.name}")

    # Parse stats from console output (if captured)
    out_path = out_dir / "agent4_is_params.json"
    out_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    return result


# ════════════════════════════════════════════════════════════════════════════
# AGENT 5 — BPD Variables + NCI_BR mapping
# ════════════════════════════════════════════════════════════════════════════

def agent_bpd_vars(twx_files: list[str], out_dir: Path) -> dict:
    step(5, "BPD-Variables", "Variables de proceso BPD + mapeo a columnas NCI_BR Appian")

    # Import the extractor directly
    script_dir = Path(__file__).parent
    sys.path.insert(0, str(script_dir))

    result = {"variables": [], "nci_br_mapped": [], "nci_br_candidates": [], "total": 0}

    try:
        from ibm_twx_tools.twx_parser import TWXParser
        from ibm_twx_tools.web_service_extractor import BPDVariableExtractor

        agg: dict[str, dict] = {}
        for twx in twx_files:
            mod = derive_module_name(twx)
            try:
                pkg = TWXParser(twx).parse()
                extractor = BPDVariableExtractor(pkg)
                vars_list = extractor.extract()
                for v in vars_list:
                    key = v.name.lower()
                    if key not in agg:
                        agg[key] = {
                            "name": v.name,
                            "direction": v.direction,
                            "is_array": v.is_array,
                            "type_name": v.type_name,
                            "frequency": v.frequency,
                            "in_nci_br": v.in_nci_br,
                            "modules": [],
                        }
                    agg[key]["frequency"] += v.frequency
                    for bpd in v.bpd_names:
                        if bpd not in agg[key].get("modules", []):
                            agg[key].setdefault("modules", []).append(bpd)
                info(f"{mod}: {len(vars_list)} vars BPD")
            except Exception as e:
                warn(f"{mod}: {e}")

        result["variables"] = sorted(agg.values(), key=lambda x: -x["frequency"])
        result["nci_br_mapped"]     = [v["name"] for v in result["variables"] if v["in_nci_br"]]
        result["nci_br_candidates"] = [v["name"] for v in result["variables"] if not v["in_nci_br"] and v["frequency"] >= 5]
        result["total"] = len(result["variables"])
        ok(f"BPD Variables: {result['total']} únicas · en NCI_BR={len(result['nci_br_mapped'])} · candidatas nuevas={len(result['nci_br_candidates'])}")

    except ImportError as e:
        warn(f"No se pudo importar extractor directamente: {e}")
        result["error"] = str(e)

    out_path = out_dir / "agent5_bpd_vars.json"
    out_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    return result


# ════════════════════════════════════════════════════════════════════════════
# AGENT 6 — Cross-Model (BOs compartidos)
# ════════════════════════════════════════════════════════════════════════════

def agent_cross_model(twx_dir: str, out_dir: Path) -> dict:
    step(6, "Cross-Model", "Business Objects compartidos entre módulos → candidatos a Toolkit Appian")

    html_path = out_dir / "cross_model_report.html"
    ok_flag, output = run_tool(
        TOOL_CMD + ["cross-model", "--dir", twx_dir, "-o", str(html_path)],
        capture=False,
    )

    result = {"html_report": str(html_path), "generated": ok_flag}
    if ok_flag:
        ok(f"Cross-model generado: {html_path.name}")
    else:
        warn("cross-model completó con avisos")

    out_path = out_dir / "agent6_cross_model.json"
    out_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    return result


# ════════════════════════════════════════════════════════════════════════════
# AGENT 7 — Parametria F3 / NOV_INSTANCE_MANAGEMENT
# ════════════════════════════════════════════════════════════════════════════

def agent_parametria(twx_files: list[str], out_dir: Path) -> dict:
    step(7, "Parametria-F3", "Arquitectura F3: clasifica BOs, detecta async Tipo 2, genera campos NOV_INSTANCE_MANAGEMENT")

    result = {"modules": {}, "summary": {"async_points": 0, "nov_fields": 0, "f3_steps": 0}}

    for twx in twx_files:
        mod = derive_module_name(twx)
        json_out = out_dir / f"f3_{mod.replace(' ','_').lower()}.json"
        ok_flag, output = run_tool(TOOL_CMD + ["parametria", twx, "-o", str(json_out)])
        if ok_flag and json_out.exists():
            try:
                data = json.loads(json_out.read_text(encoding="utf-8"))
                decomps = data.get("bpd_decompositions", [])
                nov_fields = data.get("nov_instance_management_fields", [])
                total_steps = sum(len(d.get("steps",[])) for d in decomps)
                result["modules"][mod] = {
                    "async_points": sum(d.get("async_point_count",0) for d in decomps),
                    "nov_fields": len(nov_fields),
                    "f3_steps": total_steps,
                    "bo_categories": len(data.get("bo_categories",[])),
                }
                result["summary"]["async_points"] += result["modules"][mod]["async_points"]
                result["summary"]["nov_fields"]    += len(nov_fields)
                result["summary"]["f3_steps"]      += total_steps
                ok(f"{mod}: {result['modules'][mod]['async_points']} puntos async · {total_steps} procesos F3")
            except Exception as e:
                warn(f"{mod}: {e}")
        else:
            warn(f"{mod}: parametria no disponible — {output[:60]}")

    out_path = out_dir / "agent7_parametria.json"
    out_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    ok(f"Parametria completo: {result['summary']['async_points']} puntos async · {result['summary']['f3_steps']} procesos F3 total")
    return result


# ════════════════════════════════════════════════════════════════════════════
# AGENT 8 — Appian Generator
# ════════════════════════════════════════════════════════════════════════════

def agent_appian_gen(twx_files: list[str], out_dir: Path, app_prefix: str = "") -> dict:
    step(8, "Appian-Generator", "Genera paquetes Appian importables (.zip) por módulo")

    packages_dir = out_dir / "appian_packages"
    packages_dir.mkdir(exist_ok=True)
    result = {"packages": [], "generated": 0, "failed": 0}

    for twx in twx_files:
        mod = derive_module_name(twx)
        # Derive prefix from module name if not provided
        prefix = app_prefix if app_prefix else "_".join(w[:3].upper() for w in mod.split()[:3])
        zip_out = packages_dir / f"{prefix}_appian_package.zip"

        ok_flag, output = run_tool(GEN_CMD + [
            "--twx",    twx,
            "--output", str(zip_out),
            "--prefix", prefix,
            "--app-name", mod,
        ], capture=False)

        if ok_flag and zip_out.exists():
            size_kb = round(zip_out.stat().st_size / 1024, 1)
            result["packages"].append({"module": mod, "file": zip_out.name, "size_kb": size_kb, "prefix": prefix})
            result["generated"] += 1
            ok(f"{mod} → {zip_out.name} ({size_kb} KB)")
        else:
            result["packages"].append({"module": mod, "file": "", "error": output[:120]})
            result["failed"] += 1
            warn(f"{mod}: generación falló — {output[:80]}")

    out_path = out_dir / "agent8_appian_packages.json"
    out_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    ok(f"Appian Generator: {result['generated']} paquetes generados · {result['failed']} fallidos")
    return result


# ════════════════════════════════════════════════════════════════════════════
# AGENT 9 — Master HTML Report
# ════════════════════════════════════════════════════════════════════════════

def agent_report(results: dict, out_dir: Path, twx_dir: str) -> Path:
    step(9, "Report", "Genera HTML maestro consolidado con todos los hallazgos")

    discovery   = results.get("discovery", {})
    entities    = results.get("entities", {})
    services    = results.get("services", {})
    bpd_vars    = results.get("bpd_vars", {})
    parametria  = results.get("parametria", {})
    appian      = results.get("appian", {})

    modules     = discovery.get("modules", [])
    all_bos     = entities.get("all_bos", [])
    classification = entities.get("classification", {"domain_entity":[],"dto":[],"catalog":[]})
    svc_totals  = services.get("totals", {})
    bpd_total   = bpd_vars.get("total", 0)
    nci_mapped  = bpd_vars.get("nci_br_mapped", [])
    nci_cands   = bpd_vars.get("nci_br_candidates", [])
    async_pts   = parametria.get("summary", {}).get("async_points", 0)
    f3_steps    = parametria.get("summary", {}).get("f3_steps", 0)
    packages    = appian.get("packages", [])

    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    n_modules = len(modules)

    # ── Module table rows ─────────────────────────────────────────────────
    module_rows = ""
    for m in modules:
        bt = m.get("by_type", {})
        p_data = parametria.get("modules", {}).get(m.get("name",""), {})
        pkg = next((p for p in packages if p.get("module") == m.get("name")), {})
        pkg_badge = f'<span class="badge g">✅ {pkg.get("size_kb","?")} KB</span>' if pkg.get("file") else '<span class="badge r">⏳</span>'
        module_rows += f"""
        <tr>
          <td><strong>{m.get('name','')}</strong></td>
          <td class="mono">{m.get('version','')}</td>
          <td>{m.get('total_artifacts',0)}</td>
          <td>{bt.get('business_object',0)}</td>
          <td>{bt.get('service_is',0) + bt.get('service_hhs',0) + bt.get('service_gss',0)}</td>
          <td>{bt.get('business_process',0)}</td>
          <td>{bt.get('web_service',0)}</td>
          <td>{p_data.get('async_points','-')}</td>
          <td>{pkg_badge}</td>
        </tr>"""

    # ── BO classification rows ────────────────────────────────────────────
    bo_rows = ""
    for bo in all_bos[:60]:
        cat = bo.get("_category","dto")
        cat_color = {"domain_entity":"g","dto":"b","catalog":"dim"}.get(cat,"dim")
        bo_rows += f"""<tr>
          <td><strong>{bo.get('name','')}</strong></td>
          <td><span class="badge {cat_color}">{cat}</span></td>
          <td>{len(bo.get('fields',[]))}</td>
          <td class="mono dim">{bo.get('_module','')}</td>
          <td>{'Record Type' if cat=='domain_entity' else ('CDT local' if cat=='dto' else 'skip')}</td>
        </tr>"""

    # ── Top BPD vars ──────────────────────────────────────────────────────
    bpd_rows = ""
    for v in bpd_vars.get("variables", [])[:30]:
        in_br = "✅" if v.get("in_nci_br") else ""
        cand  = "⭐" if v.get("name","").lower() in [x.lower() for x in nci_cands] else ""
        bpd_rows += f"""<tr>
          <td class="mono">{v.get('name','')}</td>
          <td><span class="badge {'b' if v.get('direction')=='IN' else 'r'}">{v.get('direction','?')}</span></td>
          <td>{v.get('type_name','')}</td>
          <td>{'[  ]' if v.get('is_array') else ''}</td>
          <td>{v.get('frequency',0)}</td>
          <td>{in_br} {cand}</td>
        </tr>"""

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8"/>
<title>Análisis Profundo IBM BPM → Appian · {now}</title>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:'Segoe UI',system-ui,sans-serif;background:#0d1117;color:#c9d1d9;line-height:1.6}}
.hero{{background:linear-gradient(135deg,#0d1117,#1a0a1e);border-bottom:2px solid #e4002b;padding:40px}}
.logo{{background:#e4002b;color:#fff;font-size:11px;font-weight:900;letter-spacing:3px;padding:8px 16px;border-radius:4px;display:inline-block;margin-bottom:16px}}
h1{{font-size:24px;color:#f0f6fc}}h1 span{{color:#e4002b}}
.sub{{color:#8b949e;font-size:13px;margin-top:4px}}
.badges{{display:flex;gap:8px;flex-wrap:wrap;margin-top:12px}}
.badge{{font-size:11px;font-weight:700;padding:3px 9px;border-radius:99px;border:1px solid}}
.badge.g{{color:#6ee7b7;border-color:rgba(16,185,129,.3);background:rgba(16,185,129,.07)}}
.badge.b{{color:#93c5fd;border-color:rgba(59,130,246,.3);background:rgba(59,130,246,.07)}}
.badge.r{{color:#fca5a5;border-color:rgba(228,0,43,.3);background:rgba(228,0,43,.07)}}
.badge.p{{color:#c4b5fd;border-color:rgba(139,92,246,.3);background:rgba(139,92,246,.07)}}
.badge.y{{color:#fde68a;border-color:rgba(245,158,11,.3);background:rgba(245,158,11,.07)}}
.badge.dim{{color:#8b949e;border-color:rgba(139,148,158,.3);background:rgba(139,148,158,.07)}}
nav{{background:#161b22;border-bottom:1px solid #30363d;padding:0 40px;position:sticky;top:0;z-index:100}}
nav a{{color:#8b949e;text-decoration:none;font-size:13px;padding:14px 14px;border-bottom:2px solid transparent;display:inline-block;white-space:nowrap}}
nav a:hover{{color:#f0f6fc;border-color:#e4002b}}
.main{{max-width:1200px;margin:0 auto;padding:40px}}
.section{{margin-bottom:48px}}
.sh{{display:flex;align-items:center;gap:12px;margin-bottom:20px;padding-bottom:12px;border-bottom:1px solid #30363d}}
.sh h2{{font-size:18px;color:#f0f6fc}}
.sh .ico{{font-size:20px}}
.stats{{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin-bottom:28px}}
.stat{{background:#161b22;border:1px solid #30363d;border-radius:8px;padding:16px;border-top:3px solid #30363d}}
.stat.g{{border-top-color:#10b981}}.stat.b{{border-top-color:#3b82f6}}.stat.r{{border-top-color:#e4002b}}
.stat.p{{border-top-color:#8b5cf6}}.stat.y{{border-top-color:#f59e0b}}.stat.c{{border-top-color:#06b6d4}}
.stat-n{{font-size:30px;font-weight:800;color:#f0f6fc}}.stat-l{{font-size:12px;color:#8b949e;margin-top:2px}}
table{{width:100%;border-collapse:collapse;font-size:13px}}
th{{background:#21262d;color:#8b949e;font-size:11px;font-weight:700;letter-spacing:.4px;text-transform:uppercase;padding:8px 12px;border-bottom:2px solid #30363d;text-align:left}}
td{{padding:8px 12px;border-bottom:1px solid #21262d}}
tr:last-child td{{border-bottom:none}}
tr:hover td{{background:rgba(255,255,255,.02)}}
.mono{{font-family:'Cascadia Code','Fira Code',monospace;font-size:12px;color:#f0883e}}
.dim{{color:#8b949e}}
.card{{background:#161b22;border:1px solid #30363d;border-radius:8px;overflow:hidden;margin-bottom:12px}}
.card-hd{{background:#21262d;padding:12px 16px;font-size:13px;font-weight:700;color:#f0f6fc;border-bottom:1px solid #30363d}}
.card-bd{{padding:16px}}
.info{{border-radius:6px;padding:14px 16px;font-size:13px;margin:12px 0;border-left:3px solid}}
.info.warn{{background:rgba(245,158,11,.06);border-color:#f59e0b;color:#fef3c7}}
.info.danger{{background:rgba(228,0,43,.06);border-color:#e4002b;color:#fee2e2}}
.info.note{{background:rgba(59,130,246,.06);border-color:#3b82f6;color:#dbeafe}}
.grid2{{display:grid;grid-template-columns:1fr 1fr;gap:16px}}
@media(max-width:768px){{.grid2{{grid-template-columns:1fr}}.main{{padding:16px}}}}
footer{{background:#161b22;border-top:1px solid #30363d;text-align:center;padding:20px;font-size:12px;color:#8b949e}}
</style>
</head>
<body>
<div class="hero">
  <div class="logo">NTT DATA</div>
  <h1>Análisis Profundo IBM BPM → <span>Appian</span></h1>
  <p class="sub">Pipeline Multi-Agente · {n_modules} módulos TWX · Generado: {now}</p>
  <div class="badges">
    <span class="badge g">✅ {n_modules} módulos</span>
    <span class="badge b">{svc_totals.get('is',0)} Integration Services</span>
    <span class="badge p">{len(all_bos)} Business Objects</span>
    <span class="badge r">{async_pts} Async Tipo 2</span>
    <span class="badge y">{bpd_total} Variables BPD</span>
    <span class="badge g">{len(packages)} paquetes Appian</span>
  </div>
</div>

<nav>
  <a href="#modules">📦 Módulos</a>
  <a href="#entities">🏗️ BOs</a>
  <a href="#services">⚙️ Services</a>
  <a href="#bpdvars">📊 BPD Vars</a>
  <a href="#parametria">🔄 F3/Async</a>
  <a href="#appian">🔷 Appian</a>
</nav>

<div class="main">

<!-- ── STATS ─────────────────────────────────────────── -->
<div class="stats">
  <div class="stat g"><div class="stat-n">{n_modules}</div><div class="stat-l">Módulos TWX</div></div>
  <div class="stat b"><div class="stat-n">{svc_totals.get('is',0)}</div><div class="stat-l">Integration Services</div></div>
  <div class="stat b"><div class="stat-n">{svc_totals.get('hhs',0)}</div><div class="stat-l">Human Services</div></div>
  <div class="stat p"><div class="stat-n">{len(all_bos)}</div><div class="stat-l">Business Objects únicos</div></div>
  <div class="stat r"><div class="stat-n">{async_pts}</div><div class="stat-l">Async Tipo 2 → NOV_IM</div></div>
  <div class="stat y"><div class="stat-n">{bpd_total}</div><div class="stat-l">Variables BPD</div></div>
  <div class="stat c"><div class="stat-n">{len(nci_mapped)}</div><div class="stat-l">Mapeadas NCI_BR</div></div>
  <div class="stat g"><div class="stat-n">{f3_steps}</div><div class="stat-l">Procesos F3 total</div></div>
  <div class="stat g"><div class="stat-n">{appian.get('generated',0)}</div><div class="stat-l">Paquetes Appian</div></div>
</div>

<!-- ── MODULES ───────────────────────────────────────── -->
<div class="section" id="modules">
  <div class="sh"><span class="ico">📦</span><h2>Inventario de módulos</h2></div>
  <table>
    <thead><tr><th>Módulo</th><th>Versión</th><th>Total arts.</th><th>BOs</th><th>Services</th><th>BPDs</th><th>WebSvcs</th><th>Async Tipo2</th><th>Appian pkg</th></tr></thead>
    <tbody>{module_rows}</tbody>
  </table>
</div>

<!-- ── ENTITIES ──────────────────────────────────────── -->
<div class="section" id="entities">
  <div class="sh"><span class="ico">🏗️</span><h2>Business Objects clasificados</h2></div>
  <div class="badges" style="margin-bottom:16px">
    <span class="badge g">domain_entity: {len(classification.get('domain_entity',[]))} → Record Type</span>
    <span class="badge b">dto: {len(classification.get('dto',[]))} → CDT local</span>
    <span class="badge dim">catalog: {len(classification.get('catalog',[]))} → skip/Constants</span>
  </div>
  <table>
    <thead><tr><th>BO Name</th><th>Categoría</th><th>Campos</th><th>Módulo origen</th><th>Target Appian</th></tr></thead>
    <tbody>{bo_rows}</tbody>
  </table>
</div>

<!-- ── SERVICES ──────────────────────────────────────── -->
<div class="section" id="services">
  <div class="sh"><span class="ico">⚙️</span><h2>Services por tipo</h2></div>
  <div class="grid2">
    <div class="card">
      <div class="card-hd">Distribución por tipo</div>
      <div class="card-bd">
        <table>
          <thead><tr><th>Tipo</th><th>Cantidad</th><th>Target Appian</th></tr></thead>
          <tbody>
            <tr><td><span class="badge b">IS</span> Integration Service</td><td><strong>{svc_totals.get('is',0)}</strong></td><td>Connected System + Integration Rule</td></tr>
            <tr><td><span class="badge g">HHS</span> Human Service</td><td><strong>{svc_totals.get('hhs',0)}</strong></td><td>Interface + Task</td></tr>
            <tr><td><span class="badge p">GSS</span> General System Service</td><td><strong>{svc_totals.get('gss',0)}</strong></td><td>Expression Rule (automática)</td></tr>
            <tr><td><strong>Total</strong></td><td><strong>{svc_totals.get('total',0)}</strong></td><td></td></tr>
          </tbody>
        </table>
      </div>
    </div>
    <div class="card">
      <div class="card-hd">Patrones de migración</div>
      <div class="card-bd" style="font-size:13px;line-height:2">
        <div>🔷 IS (processType=4) → <strong>Connected System</strong> en Appian</div>
        <div>🖥️ HHS (processType=3) → <strong>Interface + Task asignada</strong></div>
        <div>⚙️ GSS (processType=6) → <strong>Expression Rule automática</strong></div>
        <div>📋 Botones de HHS → viven en <strong>Coach Views (64.*)</strong></div>
        <div>🔗 Orden de pasos → siempre por <strong>sequenceFlow</strong></div>
      </div>
    </div>
  </div>
</div>

<!-- ── BPD VARS ───────────────────────────────────────── -->
<div class="section" id="bpdvars">
  <div class="sh"><span class="ico">📊</span><h2>Variables BPD de flujo</h2></div>
  <div class="info note">
    <strong>✅ {len(nci_mapped)} ya mapeadas en NCI_BR:</strong> {', '.join(nci_mapped[:10])}{'...' if len(nci_mapped)>10 else ''}<br/>
    <strong>⭐ {len(nci_cands)} candidatas nuevas (freq ≥5):</strong> {', '.join(nci_cands[:10])}
  </div>
  <table>
    <thead><tr><th>Variable IBM BPM</th><th>Dir.</th><th>Tipo</th><th>Array</th><th>Freq.</th><th>NCI_BR</th></tr></thead>
    <tbody>{bpd_rows}</tbody>
  </table>
</div>

<!-- ── PARAMETRIA F3 ──────────────────────────────────── -->
<div class="section" id="parametria">
  <div class="sh"><span class="ico">🔄</span><h2>Arquitectura F3 · Async Tipo 2 · NOV_INSTANCE_MANAGEMENT</h2></div>
  <div class="info warn">
    <strong>Patrón Async Tipo 2:</strong> Un WebService expone operaciones nombradas <code>respuesta*</code> → es un callback receiver → en Appian se implementa con <strong>NOV_INSTANCE_MANAGEMENT</strong> (tabla de instancias + timer event para polling del padre).
  </div>
  <table>
    <thead><tr><th>Módulo</th><th>Puntos async</th><th>Procesos F3</th><th>Campos NOV_IM</th><th>BOs clasificados</th></tr></thead>
    <tbody>
{''.join(f"""<tr><td><strong>{mod}</strong></td><td>{d.get('async_points',0)}</td><td>{d.get('f3_steps',0)}</td><td>{d.get('nov_fields',0)}</td><td>{d.get('bo_categories',0)}</td></tr>""" for mod, d in parametria.get('modules',{}).items())}
    </tbody>
  </table>
</div>

<!-- ── APPIAN PACKAGES ────────────────────────────────── -->
<div class="section" id="appian">
  <div class="sh"><span class="ico">🔷</span><h2>Paquetes Appian generados</h2></div>
  <table>
    <thead><tr><th>Módulo</th><th>Prefix</th><th>Archivo ZIP</th><th>Tamaño</th><th>Estado</th></tr></thead>
    <tbody>
{''.join(f"""<tr><td><strong>{p.get('module','')}</strong></td><td class="mono">{p.get('prefix','')}</td><td class="mono">{p.get('file','—')}</td><td>{p.get('size_kb','—')} KB</td><td>{'<span class="badge g">✅ OK</span>' if p.get('file') else '<span class="badge r">❌ Error</span>'}</td></tr>""" for p in packages)}
    </tbody>
  </table>
</div>

</div><!-- /main -->
<footer>
  <strong style="color:#e4002b">NTT DATA</strong> · IBM BPM → Appian · Pipeline Multi-Agente v{VERSION} · {now}
</footer>
<script>
document.querySelectorAll('nav a').forEach(a=>{{
  a.addEventListener('click',e=>{{
    e.preventDefault();
    document.querySelector(a.getAttribute('href'))?.scrollIntoView({{behavior:'smooth',block:'start'}});
  }});
}});
</script>
</body></html>"""

    report_path = out_dir / "pipeline_master_report.html"
    report_path.write_text(html, encoding="utf-8")
    ok(f"Reporte maestro: {report_path}")
    return report_path


# ════════════════════════════════════════════════════════════════════════════
# ORCHESTRATOR
# ════════════════════════════════════════════════════════════════════════════

def orchestrate(twx_dir: str, out_dir: Path, agents: list[int], app_prefix: str = ""):
    """Main orchestrator — runs all agents in sequence."""
    banner()

    # Discover TWX files
    twx_files = sorted(glob.glob(os.path.join(twx_dir, "**", "*.twx"), recursive=True))
    if not twx_files:
        twx_files = sorted(glob.glob(os.path.join(twx_dir, "*.twx")))

    if not twx_files:
        err(f"No se encontraron archivos .twx en: {twx_dir}")
        sys.exit(1)

    print(f"\n  {C}📂  Directorio:{RESET} {twx_dir}")
    print(f"  {C}📦  Módulos encontrados:{RESET} {len(twx_files)}")
    for f in twx_files:
        print(f"       {DIM}· {derive_module_name(f)}{RESET}")
    print(f"\n  {C}💾  Output:{RESET} {out_dir}")
    print(f"  {C}🤖  Agentes activos:{RESET} {agents}")

    out_dir.mkdir(parents=True, exist_ok=True)

    results     = {}
    start_time  = time.time()

    if 1 in agents:
        results["discovery"]   = agent_discovery(twx_files, out_dir)
    if 2 in agents:
        results["entities"]    = agent_entities(twx_files, out_dir)
    if 3 in agents:
        results["services"]    = agent_services(twx_files, out_dir)
    if 4 in agents:
        results["is_params"]   = agent_is_params(twx_dir, out_dir)
    if 5 in agents:
        results["bpd_vars"]    = agent_bpd_vars(twx_files, out_dir)
    if 6 in agents:
        results["cross_model"] = agent_cross_model(twx_dir, out_dir)
    if 7 in agents:
        results["parametria"]  = agent_parametria(twx_files, out_dir)
    if 8 in agents:
        results["appian"]      = agent_appian_gen(twx_files, out_dir, app_prefix)
    if 9 in agents:
        report_path = agent_report(results, out_dir, twx_dir)

    elapsed = round(time.time() - start_time, 1)

    print(f"""
{G}╔══════════════════════════════════════════════════════════════════════════╗{RESET}
{G}║{RESET}  {W}Pipeline completado en {elapsed}s{RESET}                                              {G}║{RESET}
{G}║{RESET}  {W}Outputs en:{RESET} {str(out_dir)[:60]}   {G}║{RESET}
{G}╚══════════════════════════════════════════════════════════════════════════╝{RESET}
""")
    return results


# ════════════════════════════════════════════════════════════════════════════
# CLI
# ════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        prog="pipeline_orchestrator",
        description=f"{CORPORATE} IBM BPM → Appian · Pipeline Multi-Agente v{VERSION}",
    )
    parser.add_argument("--dir",     required=True, help="Directorio con archivos .twx")
    parser.add_argument("--output",  default=None,  help="Directorio de salida (default: <dir>/pipeline_output/)")
    parser.add_argument("--prefix",  default="",    help="Prefijo Appian (ej: NCI_RB)")
    parser.add_argument("--agents",  default="1,2,3,4,5,6,7,8,9",
                        help="Agentes a ejecutar, separados por coma (default: todos)")
    parser.add_argument("--only",    default=None,
                        help="Atajo: is-params | cross-model | appian | report")

    args = parser.parse_args()

    twx_dir = args.dir
    out_dir = Path(args.output) if args.output else Path(twx_dir) / "pipeline_output"

    # Parse agents
    if args.only:
        shortcuts = {"is-params": [4,9], "cross-model": [6,9], "appian": [8,9], "report": [9],
                     "entities": [2,9], "services": [3,9], "bpd": [5,9], "f3": [7,9]}
        agents = shortcuts.get(args.only, [int(x) for x in args.agents.split(",") if x.strip()])
    else:
        agents = [int(x) for x in args.agents.split(",") if x.strip()]

    orchestrate(twx_dir, out_dir, agents=agents, app_prefix=args.prefix)


if __name__ == "__main__":
    main()
