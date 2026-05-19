#!/usr/bin/env python3
"""
NTTDATA IBM TWX — Generador de Reporte HTML
============================================
Lee los archivos de salida de run_analysis.py y genera un reporte HTML
con el mismo estilo profesional de la Arquitectura de Conocimiento v3.

Uso:
    python -m ibm_twx_tools html_report <output_dir>
    python generate_html_report.py <output_dir>
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


# ── Helpers ───────────────────────────────────────────────────────────────────

def _load_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _load_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return ""


def _esc(s) -> str:
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _badge(text: str, color: str = "blue") -> str:
    colors = {
        "blue":   ("dbeafe", "1e40af"),
        "green":  ("dcfce7", "166534"),
        "amber":  ("fef3c7", "92400e"),
        "red":    ("fee2e2", "991b1b"),
        "gray":   ("f1f5f9", "475569"),
        "teal":   ("ccfbf1", "134e4a"),
        "purple": ("ede9fe", "5b21b6"),
    }
    bg, fg = colors.get(color, colors["blue"])
    return (f'<span style="display:inline-block;padding:2px 8px;border-radius:10px;'
            f'font-size:10px;font-weight:600;background:#{bg};color:#{fg}">{_esc(text)}</span>')


# ── CSS + Shell del documento ─────────────────────────────────────────────────

_CSS = """
:root {
  --bd: #0a2540; --bm: #1a3a5c; --bl: #2563eb;
  --teal: #0d9488; --amber: #d97706; --red: #dc2626;
  --green: #16a34a; --purple: #7c3aed; --gbg: #f8fafc;
  --gbrd: #e2e8f0; --tx: #1e293b; --mu: #64748b;
}
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:'Segoe UI',system-ui,sans-serif;font-size:13px;color:var(--tx);background:#f1f5f9}
header{background:var(--bd);color:white;padding:24px 36px;border-bottom:3px solid var(--bl)}
header h1{font-size:20px;font-weight:700;margin-bottom:6px}
header .sub{font-size:12px;color:#94a3b8;margin-bottom:12px}
.meta-row{display:flex;gap:10px;flex-wrap:wrap}
.mp{background:rgba(255,255,255,.12);border-radius:20px;padding:3px 12px;font-size:11px}
.mp.hl{background:var(--bl);color:white}
nav{background:var(--bm);padding:0 36px;display:flex;flex-wrap:wrap}
nav a{color:#cbd5e1;text-decoration:none;padding:9px 13px;font-size:11px;transition:.2s}
nav a:hover{background:rgba(255,255,255,.1);color:white}
.container{max-width:1400px;margin:0 auto;padding:24px 36px}
section{background:white;border-radius:10px;box-shadow:0 1px 4px rgba(0,0,0,.09);margin-bottom:24px;overflow:hidden}
.sh{background:var(--bd);color:white;padding:14px 20px;display:flex;align-items:center;gap:12px}
.sh h2{font-size:14px;font-weight:600}
.sh .cnt{background:rgba(255,255,255,.18);border-radius:12px;padding:2px 10px;font-size:11px}
.sb{padding:20px}
table{width:100%;border-collapse:collapse;font-size:12px;margin:8px 0}
th{background:var(--bd);color:white;padding:7px 11px;text-align:left;font-size:11px;font-weight:600}
td{padding:6px 11px;border-bottom:1px solid var(--gbrd);vertical-align:top}
tr:last-child td{border-bottom:none}
tr:nth-child(even){background:#f8fafc}
tr:hover{background:#eff6ff}
.card{background:var(--gbg);border:1px solid var(--gbrd);border-radius:8px;padding:14px}
.card h4{font-size:12px;font-weight:700;color:var(--bd);margin-bottom:8px;border-bottom:1px solid var(--gbrd);padding-bottom:5px}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:14px}
.grid3{display:grid;grid-template-columns:1fr 1fr 1fr;gap:14px}
.grid4{display:grid;grid-template-columns:repeat(4,1fr);gap:12px}
.stat{background:var(--gbg);border:1px solid var(--gbrd);border-radius:8px;padding:14px;text-align:center}
.stat-n{font-size:28px;font-weight:800;color:var(--bl)}
.stat-l{font-size:11px;color:var(--mu);margin-top:4px}
code{font-family:'Cascadia Code','Consolas',monospace;background:#1e293b;color:#e2e8f0;
     padding:2px 6px;border-radius:3px;font-size:11px}
.mono{font-family:'Cascadia Code','Consolas',monospace;font-size:11px;background:#0f172a;
      color:#e2e8f0;border-radius:8px;padding:14px;line-height:1.7;overflow-x:auto;white-space:pre-wrap}
.tag-is{color:#1d4ed8;font-weight:700} .tag-hhs{color:#0d9488;font-weight:700}
.tag-gss{color:#7c3aed;font-weight:700} .tag-uca{color:#d97706;font-weight:700}
.tag-bo{color:#16a34a;font-weight:700}  .tag-bpd{color:#db2777;font-weight:700}
.alert{background:#fef3c7;border-left:4px solid var(--amber);padding:10px 14px;border-radius:4px;margin:10px 0;font-size:12px}
.alert-i{background:#dbeafe;border-left:4px solid var(--bl);padding:10px 14px;border-radius:4px;margin:10px 0;font-size:12px}
.alert-g{background:#dcfce7;border-left:4px solid var(--green);padding:10px 14px;border-radius:4px;margin:10px 0;font-size:12px}
h3{font-size:13px;color:var(--bd);font-weight:700;margin:16px 0 8px}
h3:first-child{margin-top:0}
footer{background:var(--bd);color:#64748b;text-align:center;padding:16px;font-size:11px;margin-top:28px}
"""


def _page_open(twx_name: str, now: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Extracción Técnica — {_esc(twx_name)}</title>
<style>{_CSS}</style>
</head>
<body>
<header>
  <h1>Reporte de Extracción Técnica — <em>{_esc(twx_name)}</em></h1>
  <p class="sub">Análisis automático completo · NTTDATA IBM TWX Reverse Engineering Suite v1.0.0</p>
  <div class="meta-row">
    <span class="mp">Fuente: {_esc(twx_name)}</span>
    <span class="mp hl">9 Ciclos · Metodología v3</span>
    <span class="mp">Generado: {_esc(now)}</span>
    <span class="mp">NTT DATA EMEAL</span>
  </div>
</header>
<nav>
  <a href="#s1">Resumen</a>
  <a href="#s2">Business Objects</a>
  <a href="#s3">Servicios</a>
  <a href="#s4">Endpoints</a>
  <a href="#s5">Entry Points</a>
  <a href="#s6">Flujos</a>
  <a href="#s7">Dependencias</a>
  <a href="#s8">Scripts</a>
  <a href="#s9">Documentación</a>
</nav>
<div class="container">
"""


def _page_close(twx_name: str, now: str) -> str:
    return f"""
</div>
<footer>
  Generado por NTTDATA IBM TWX Reverse Engineering Suite v1.0.0 &nbsp;·&nbsp;
  {_esc(twx_name)} &nbsp;·&nbsp; {_esc(now)} &nbsp;·&nbsp; NTT DATA EMEAL
</footer>
</body></html>
"""


# ── Secciones ─────────────────────────────────────────────────────────────────

def _section_summary(data) -> str:
    if not data:
        return "<section id='s1'><div class='sh'><h2>1. Resumen</h2></div><div class='sb'><p>No disponible</p></div></section>"

    name    = _esc(data.get("name", "—"))
    version = _esc(str(data.get("version", "—")))
    counts  = data.get("counts", {})

    stats = [
        (counts.get("GSS", 0),  "GSS",         "teal"),
        (counts.get("HHS", 0),  "HHS",         "green"),
        (counts.get("IS",  0),  "IS",          "blue"),
        (counts.get("UCA", 0),  "UCAs",        "amber"),
        (counts.get("BO",  0),  "Business Obj","purple"),
        (counts.get("BPD", 0),  "BPDs",        "red"),
        (counts.get("CoachView", 0), "Coach Views","gray"),
    ]
    stats_html = "".join(
        f'<div class="stat"><div class="stat-n">{n}</div><div class="stat-l">{l}</div></div>'
        for n, l, _ in stats
    )

    total = sum(c for c, _, _ in stats)
    return f"""
<section id="s1">
  <div class="sh">
    <h2>1. Resumen del proceso</h2>
    <span class="cnt">{total} artefactos totales</span>
  </div>
  <div class="sb">
    <div class="alert-i">
      <strong>Proceso:</strong> {name} &nbsp;·&nbsp; <strong>Versión:</strong> {version}
    </div>
    <div class="grid4" style="margin-top:14px">{stats_html}</div>
  </div>
</section>
"""


def _section_entities(data) -> str:
    if not data:
        return ""
    rows = []
    for bo in data[:60]:
        n = _esc(bo.get("name", "—"))
        ns = _esc(bo.get("namespace", "—"))
        fields = bo.get("fields", [])
        fc = len(fields)
        parent = _esc(bo.get("parent", "") or "—")
        field_list = ", ".join(_esc(f.get("name","?")) for f in fields[:6])
        if len(fields) > 6:
            field_list += f" … (+{len(fields)-6})"
        rows.append(
            f"<tr><td><code>{n}</code></td><td>{ns}</td>"
            f"<td>{parent}</td><td>{fc}</td>"
            f"<td style='color:#64748b;font-size:11px'>{field_list}</td></tr>"
        )
    table = (
        "<table><tr><th>Nombre</th><th>Namespace</th><th>Herencia</th>"
        "<th>#Campos</th><th>Campos</th></tr>"
        + "".join(rows) + "</table>"
    )
    return f"""
<section id="s2">
  <div class="sh">
    <h2>2. Business Objects</h2>
    <span class="cnt">{len(data)} BOs</span>
  </div>
  <div class="sb">{table}</div>
</section>
"""


def _section_services(data) -> str:
    if not data:
        return ""

    by_type: dict[str, list] = {}
    for svc in data:
        t = svc.get("type", "?")
        by_type.setdefault(t, []).append(svc)

    sections_html = ""
    colors = {"HHS": "teal", "IS": "blue", "GSS": "purple"}
    for stype, svcs in by_type.items():
        color = colors.get(stype, "gray")
        rows = []
        for s in svcs[:40]:
            rows.append(
                f"<tr><td><code>{_esc(s.get('name','—'))}</code></td>"
                f"<td>{_esc(s.get('subtype','—'))}</td>"
                f"<td>{len(s.get('steps',[]))}</td>"
                f"<td style='color:#64748b;font-size:11px'>{_esc(str(s.get('description',''))[:80])}</td></tr>"
            )
        sections_html += f"""
<h3><span class="tag-{stype.lower()}">{stype}</span> — {len(svcs)} servicios</h3>
<table><tr><th>Nombre</th><th>Subtipo</th><th>#Pasos</th><th>Descripción</th></tr>
{''.join(rows)}</table>"""

    return f"""
<section id="s3">
  <div class="sh">
    <h2>3. Servicios</h2>
    <span class="cnt">{len(data)} servicios</span>
  </div>
  <div class="sb">{sections_html}</div>
</section>
"""


def _section_endpoints(data) -> str:
    if not data:
        return ""
    rows = []
    for ep in data[:50]:
        rows.append(
            f"<tr><td><code>{_esc(ep.get('name','—'))}</code></td>"
            f"<td>{_esc(ep.get('type','—'))}</td>"
            f"<td style='font-size:11px;color:#64748b'>{_esc(ep.get('url','—'))}</td>"
            f"<td>{_esc(ep.get('operation','—'))}</td></tr>"
        )
    table = ("<table><tr><th>Nombre</th><th>Tipo</th><th>URL / WSDL</th><th>Operación</th></tr>"
             + "".join(rows) + "</table>")
    return f"""
<section id="s4">
  <div class="sh">
    <h2>4. Endpoints externos</h2>
    <span class="cnt">{len(data)} endpoints</span>
  </div>
  <div class="sb">{table}</div>
</section>
"""


def _section_entries(data) -> str:
    if not data:
        return ""
    rows = []
    for e in data[:40]:
        rows.append(
            f"<tr><td><code>{_esc(e.get('name','—'))}</code></td>"
            f"<td>{_esc(e.get('type','—'))}</td>"
            f"<td style='font-size:11px'>{_esc(e.get('queue','—'))}</td>"
            f"<td style='font-size:11px;color:#64748b'>{_esc(str(e.get('message',''))[:100])}</td></tr>"
        )
    table = ("<table><tr><th>Nombre</th><th>Tipo</th><th>Cola / Evento</th><th>Mensaje</th></tr>"
             + "".join(rows) + "</table>")
    return f"""
<section id="s5">
  <div class="sh">
    <h2>5. Entry Points / UCAs</h2>
    <span class="cnt">{len(data)} entradas</span>
  </div>
  <div class="sb">{table}</div>
</section>
"""


def _section_flows(text: str) -> str:
    if not text.strip():
        return ""
    preview = _esc(text[:3000]) + ("…" if len(text) > 3000 else "")
    return f"""
<section id="s6">
  <div class="sh">
    <h2>6. Flujos de proceso (Mermaid)</h2>
    <span class="cnt">diagramas</span>
  </div>
  <div class="sb">
    <div class="alert-i">Estos diagramas pueden pegarse en cualquier editor Mermaid
    (mermaid.live, VS Code, Copilot) para visualización gráfica.</div>
    <div class="mono">{preview}</div>
  </div>
</section>
"""


def _section_deps(text: str) -> str:
    if not text.strip():
        return ""
    preview = _esc(text[:2000]) + ("…" if len(text) > 2000 else "")
    return f"""
<section id="s7">
  <div class="sh">
    <h2>7. Grafo de dependencias</h2>
  </div>
  <div class="sb">
    <div class="mono">{preview}</div>
  </div>
</section>
"""


def _section_scripts(text: str) -> str:
    if not text.strip():
        return ""
    lines = text.splitlines()
    preview = _esc("\n".join(lines[:80])) + (f"\n… ({len(lines)} líneas totales)" if len(lines) > 80 else "")
    return f"""
<section id="s8">
  <div class="sh">
    <h2>8. Scripts embebidos</h2>
    <span class="cnt">{len(lines)} líneas</span>
  </div>
  <div class="sb">
    <div class="alert">Los scripts JavaScript están embebidos en los nodos de Gateway/Script de los BPDs.</div>
    <div class="mono">{preview}</div>
  </div>
</section>
"""


def _section_docs(text: str) -> str:
    if not text.strip():
        return ""
    # Convertir Markdown básico a HTML
    html_lines = []
    for line in text.splitlines()[:300]:
        el = _esc(line)
        if line.startswith("### "):
            el = f"<h3>{_esc(line[4:])}</h3>"
        elif line.startswith("## "):
            el = f"<h3 style='font-size:14px'>{_esc(line[3:])}</h3>"
        elif line.startswith("# "):
            el = f"<h3 style='font-size:15px;color:#1e3a5f'>{_esc(line[2:])}</h3>"
        elif line.startswith("- ") or line.startswith("* "):
            el = f"<div style='padding:2px 0 2px 14px'>· {_esc(line[2:])}</div>"
        elif line.startswith("|"):
            el = f"<div style='font-family:monospace;font-size:11px;color:#475569'>{_esc(line)}</div>"
        elif line.strip() == "":
            el = "<br>"
        else:
            el = f"<p style='margin:4px 0'>{_esc(line)}</p>"
        html_lines.append(el)

    total_lines = len(text.splitlines())
    return f"""
<section id="s9">
  <div class="sh">
    <h2>9. Documentación completa (Markdown)</h2>
    <span class="cnt">{total_lines} líneas</span>
  </div>
  <div class="sb">
    {''.join(html_lines)}
    {'<div class="alert">⋯ documento truncado para visualización (primeras 300 líneas)</div>' if total_lines > 300 else ''}
  </div>
</section>
"""


# ── Función principal ─────────────────────────────────────────────────────────

def generate_report(out_dir: Path, twx_name: str) -> Path:
    """Lee los outputs de run_analysis.py y genera el reporte HTML."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    analyze   = _load_json(out_dir / "01_analyze.json")
    entities  = _load_json(out_dir / "02_entities.json")
    services  = _load_json(out_dir / "03_services.json")
    endpoints = _load_json(out_dir / "04_endpoints.json")
    entries   = _load_json(out_dir / "05_entries.json")
    flows_txt = _load_text(out_dir / "06_flows.txt")
    deps_txt  = _load_text(out_dir / "07_deps.txt")
    scripts   = _load_text(out_dir / "08_scripts.txt")
    docs_md   = _load_text(out_dir / "09_docs.md")

    html = (
        _page_open(twx_name, now)
        + _section_summary(analyze)
        + _section_entities(entities or [])
        + _section_services(services or [])
        + _section_endpoints(endpoints or [])
        + _section_entries(entries or [])
        + _section_flows(flows_txt)
        + _section_deps(deps_txt)
        + _section_scripts(scripts)
        + _section_docs(docs_md)
        + _page_close(twx_name, now)
    )

    report_path = out_dir / f"{twx_name}_ExtraccionTecnica.html"
    report_path.write_text(html, encoding="utf-8")
    return report_path


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Uso: python html_report.py <output_dir> [twx_name]")
        sys.exit(1)
    out = Path(sys.argv[1])
    name = sys.argv[2] if len(sys.argv) > 2 else out.name
    p = generate_report(out, name)
    print(f"Reporte generado: {p}")
