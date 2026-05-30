"""
NTTDATA IBM TWX — Cross-Model HTML Report Generator
====================================================
Genera un reporte HTML de alta calidad UX/UI para el análisis de patrones
de modelo de datos cruzado entre N ficheros .twx.

Secciones:
  1. Resumen ejecutivo con métricas y score de reutilización
  2. Business Objects compartidos / reutilizables
  3. Clusters estructurales (misma estructura, diferente nombre)
  4. Business Objects únicos por TWX
  5. Modelo completo por TWX (colapsable)
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .cross_model_analyzer import CrossModelReport


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _esc(s) -> str:
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _badge(text: str, color: str = "blue") -> str:
    palette = {
        "blue":   ("dbeafe", "1e40af"),
        "green":  ("dcfce7", "166534"),
        "amber":  ("fef3c7", "92400e"),
        "red":    ("fee2e2", "991b1b"),
        "gray":   ("f1f5f9", "475569"),
        "teal":   ("ccfbf1", "134e4a"),
        "purple": ("ede9fe", "5b21b6"),
        "rose":   ("ffe4e6", "9f1239"),
        "indigo": ("e0e7ff", "3730a3"),
    }
    bg, fg = palette.get(color, palette["blue"])
    return (
        f'<span style="display:inline-block;padding:2px 9px;border-radius:12px;'
        f'font-size:10px;font-weight:700;letter-spacing:.3px;'
        f'background:#{bg};color:#{fg}">{_esc(text)}</span>'
    )


def _pct_bar(value: int, total: int, color: str = "#2563eb") -> str:
    if total == 0:
        return ""
    pct = min(100, round(value / total * 100))
    return (
        f'<div style="display:flex;align-items:center;gap:8px;margin-top:4px">'
        f'<div style="flex:1;background:#e2e8f0;border-radius:99px;height:6px;overflow:hidden">'
        f'<div style="width:{pct}%;height:100%;background:{color};border-radius:99px;'
        f'transition:width .4s ease"></div></div>'
        f'<span style="font-size:11px;font-weight:700;color:{color};min-width:32px">{pct}%</span>'
        f'</div>'
    )


# ─────────────────────────────────────────────────────────────────────────────
# CSS
# ─────────────────────────────────────────────────────────────────────────────

_CSS = """
:root {
  --navy: #0a2540; --navy-m: #1a3a5c; --navy-l: #234876;
  --blue:  #2563eb; --blue-l: #3b82f6; --blue-xl: #dbeafe;
  --teal:  #0d9488; --teal-l: #ccfbf1;
  --green: #16a34a; --green-l: #dcfce7;
  --amber: #d97706; --amber-l: #fef3c7;
  --red:   #dc2626; --red-l:   #fee2e2;
  --purple:#7c3aed; --purple-l:#ede9fe;
  --bg:    #f1f5f9; --surface: #ffffff;
  --border:#e2e8f0; --muted:   #64748b;
  --tx:    #1e293b; --tx-s:    #475569;
}
*{box-sizing:border-box;margin:0;padding:0}
html{scroll-behavior:smooth}
body{font-family:'Segoe UI',system-ui,-apple-system,sans-serif;font-size:13px;
     color:var(--tx);background:var(--bg);line-height:1.5}

/* ── Header ── */
header{background:linear-gradient(135deg,var(--navy) 0%,var(--navy-m) 60%,#1e3a6e 100%);
       color:white;padding:28px 40px 20px;position:relative;overflow:hidden}
header::after{content:'';position:absolute;right:-40px;top:-40px;width:260px;height:260px;
              background:rgba(37,99,235,.15);border-radius:50%}
header::before{content:'';position:absolute;right:100px;bottom:-60px;width:180px;height:180px;
               background:rgba(13,148,136,.1);border-radius:50%}
header h1{font-size:22px;font-weight:800;letter-spacing:-.3px;margin-bottom:4px;position:relative}
header .subtitle{font-size:12px;color:#94a3b8;margin-bottom:14px;position:relative}
.meta-row{display:flex;gap:8px;flex-wrap:wrap;position:relative}
.mp{background:rgba(255,255,255,.13);border:1px solid rgba(255,255,255,.18);
    border-radius:20px;padding:3px 12px;font-size:11px;backdrop-filter:blur(4px)}
.mp.hl{background:var(--blue);border-color:var(--blue-l);font-weight:600}
.mp.tl{background:rgba(13,148,136,.3);border-color:var(--teal)}

/* ── Nav ── */
nav{background:var(--navy-m);padding:0 40px;display:flex;flex-wrap:wrap;
    border-bottom:2px solid rgba(37,99,235,.4);position:sticky;top:0;z-index:100}
nav a{color:#94a3b8;text-decoration:none;padding:10px 14px;font-size:11px;
      font-weight:500;transition:all .2s;border-bottom:2px solid transparent;
      margin-bottom:-2px;white-space:nowrap}
nav a:hover,nav a.active{color:white;border-bottom-color:var(--blue-l)}

/* ── Layout ── */
.container{max-width:1440px;margin:0 auto;padding:28px 40px}

/* ── Sections ── */
.section{background:var(--surface);border-radius:12px;
         box-shadow:0 1px 3px rgba(0,0,0,.07),0 4px 16px rgba(0,0,0,.04);
         margin-bottom:24px;overflow:hidden}
.sh{background:var(--navy);color:white;padding:14px 22px;
    display:flex;align-items:center;gap:12px}
.sh .icon{font-size:18px;opacity:.9}
.sh h2{font-size:14px;font-weight:700;flex:1}
.sh .cnt{background:rgba(255,255,255,.18);border-radius:12px;
         padding:3px 11px;font-size:11px;font-weight:600;white-space:nowrap}
.sb{padding:22px}

/* ── Stats grid ── */
.stats-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:14px;margin-bottom:20px}
.stat-card{background:var(--bg);border:1px solid var(--border);border-radius:10px;
           padding:16px 20px;text-align:center;position:relative;overflow:hidden}
.stat-card::before{content:'';position:absolute;top:0;left:0;right:0;height:3px}
.stat-card.blue::before{background:var(--blue)}
.stat-card.green::before{background:var(--green)}
.stat-card.amber::before{background:var(--amber)}
.stat-card.teal::before{background:var(--teal)}
.stat-card.purple::before{background:var(--purple)}
.stat-card.red::before{background:var(--red)}
.stat-n{font-size:32px;font-weight:800;line-height:1;margin-bottom:4px}
.stat-n.blue{color:var(--blue)} .stat-n.green{color:var(--green)}
.stat-n.amber{color:var(--amber)} .stat-n.teal{color:var(--teal)}
.stat-n.purple{color:var(--purple)} .stat-n.red{color:var(--red)}
.stat-l{font-size:11px;color:var(--muted);font-weight:500}

/* ── Reusability score ── */
.score-bar{background:var(--bg);border:1px solid var(--border);border-radius:10px;padding:18px 22px;margin-top:4px}
.score-bar h4{font-size:12px;font-weight:700;color:var(--navy);margin-bottom:12px}
.bar-row{display:flex;align-items:center;gap:10px;margin-bottom:8px}
.bar-label{font-size:11px;color:var(--tx-s);width:180px;flex-shrink:0}
.bar-track{flex:1;background:var(--border);border-radius:99px;height:8px;overflow:hidden}
.bar-fill{height:100%;border-radius:99px;transition:width .5s ease}
.bar-pct{font-size:11px;font-weight:700;min-width:36px;text-align:right}

/* ── Tables ── */
table{width:100%;border-collapse:collapse;font-size:12px}
th{background:var(--navy);color:white;padding:8px 12px;text-align:left;
   font-size:11px;font-weight:600;letter-spacing:.3px;white-space:nowrap}
td{padding:7px 12px;border-bottom:1px solid var(--border);vertical-align:top}
tr:last-child td{border-bottom:none}
tr:nth-child(even) td{background:#f8fafc}
tr:hover td{background:#eff6ff}
.tbl-wrap{border-radius:8px;overflow:hidden;border:1px solid var(--border)}

/* ── Cards ── */
.card{background:var(--bg);border:1px solid var(--border);border-radius:10px;padding:16px;margin-bottom:12px}
.card-header{display:flex;align-items:center;gap:8px;margin-bottom:10px;
             padding-bottom:8px;border-bottom:1px solid var(--border)}
.card-header h4{font-size:13px;font-weight:700;color:var(--navy);flex:1}
.card.identical{border-left:4px solid var(--green)}
.card.divergent{border-left:4px solid var(--amber)}

/* ── Cluster card ── */
.cluster-card{background:var(--bg);border:1px solid var(--border);border-radius:10px;
              margin-bottom:14px;overflow:hidden}
.cluster-header{background:linear-gradient(90deg,var(--navy-l),var(--navy-m));
                color:white;padding:10px 16px;display:flex;align-items:center;gap:10px}
.cluster-id{background:var(--blue);border-radius:50%;width:24px;height:24px;
            display:flex;align-items:center;justify-content:center;
            font-size:11px;font-weight:800;flex-shrink:0}
.cluster-sig{font-size:11px;color:#cbd5e1;font-family:'Cascadia Code','Consolas',monospace;
             margin-top:2px;word-break:break-all}

/* ── Details/Accordion ── */
details{border:1px solid var(--border);border-radius:8px;margin-bottom:8px;overflow:hidden}
details[open]{box-shadow:0 2px 8px rgba(0,0,0,.06)}
summary{background:var(--bg);padding:10px 14px;cursor:pointer;
        font-size:12px;font-weight:600;color:var(--navy);
        display:flex;align-items:center;gap:8px;list-style:none;
        border-bottom:1px solid transparent;transition:background .15s}
summary::-webkit-details-marker{display:none}
summary::before{content:'▶';font-size:9px;color:var(--muted);transition:transform .2s;flex-shrink:0}
details[open] summary::before{transform:rotate(90deg)}
details[open] summary{background:#f0f7ff;border-bottom-color:var(--border);color:var(--blue)}
.details-body{padding:14px}

/* ── Unique list ── */
.unique-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:8px}
.unique-pill{background:var(--bg);border:1px solid var(--border);border-radius:6px;
             padding:6px 10px;font-size:11px;font-family:'Cascadia Code','Consolas',monospace;
             color:var(--navy-l);display:flex;align-items:center;gap:6px}
.unique-pill::before{content:'◆';font-size:8px;color:var(--muted)}

/* ── Divider ── */
.divider{border:none;border-top:1px solid var(--border);margin:16px 0}

/* ── Alerts ── */
.alert{display:flex;gap:10px;padding:10px 14px;border-radius:8px;font-size:12px;margin-bottom:14px}
.alert.info{background:var(--blue-xl);border-left:3px solid var(--blue);color:#1e3a8a}
.alert.success{background:var(--green-l);border-left:3px solid var(--green);color:#14532d}
.alert.warn{background:var(--amber-l);border-left:3px solid var(--amber);color:#78350f}
.alert .alert-icon{font-size:14px;flex-shrink:0}

/* ── Code ── */
code{font-family:'Cascadia Code','Consolas',monospace;background:#1e293b;color:#e2e8f0;
     padding:1px 6px;border-radius:4px;font-size:11px}
.sig-code{font-family:'Cascadia Code','Consolas',monospace;font-size:10px;
          background:#0f172a;color:#7dd3fc;padding:4px 8px;border-radius:4px;
          word-break:break-all;display:block;margin-top:4px}

/* ── TWX file list ── */
.file-list{display:flex;flex-direction:column;gap:6px;margin:12px 0}
.file-item{display:flex;align-items:center;gap:10px;background:var(--bg);
           border:1px solid var(--border);border-radius:8px;padding:8px 14px}
.file-item .file-icon{font-size:16px}
.file-item .file-name{font-size:12px;font-weight:600;color:var(--navy)}
.file-item .file-path{font-size:10px;color:var(--muted)}

/* ── Field diff table ── */
.diff-identical td:last-child{color:var(--green);font-weight:600}
.diff-diverge   td:last-child{color:var(--amber);font-weight:600}

/* ── Footer ── */
footer{background:var(--navy);color:#64748b;text-align:center;
       padding:18px 40px;font-size:11px;margin-top:12px}
footer span{color:#94a3b8}
"""


# ─────────────────────────────────────────────────────────────────────────────
# Page chrome
# ─────────────────────────────────────────────────────────────────────────────

def _page_open(report: "CrossModelReport", now: str) -> str:
    files_html = "".join(
        f'<span class="mp">📦 {_esc(p.split("/")[-1].split(chr(92))[-1])}</span>'
        for p in report.twx_files
    )
    n = len(report.twx_files)
    stats = report.stats
    total_bo = stats.get("total_distinct_bo_names", 0)
    shared   = stats.get("shared_across_files", 0)
    pct      = round(shared / total_bo * 100) if total_bo else 0
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Cross-Model Analysis — NTTDATA TWX Suite</title>
<style>{_CSS}</style>
</head>
<body>
<header>
  <h1>🔍 Cross-TWX Data Model Pattern Analysis</h1>
  <p class="subtitle">
    Análisis de patrones de modelo de datos cruzado &nbsp;·&nbsp;
    NTTDATA IBM TWX Reverse Engineering Suite v1.0.0
  </p>
  <div class="meta-row">
    <span class="mp hl">📊 {n} ficheros analizados</span>
    <span class="mp tl">♻️ {pct}% reutilización</span>
    <span class="mp">🕒 {_esc(now)}</span>
    <span class="mp">NTT DATA EMEAL</span>
    {files_html}
  </div>
</header>
<nav>
  <a href="#s1">📊 Resumen</a>
  <a href="#s2">♻️ Compartidos</a>
  <a href="#s3">🔗 Clusters</a>
  <a href="#s4">🔒 Únicos</a>
  <a href="#s5">📐 Modelo completo</a>
</nav>
<div class="container">
"""


def _page_close(now: str) -> str:
    return f"""
</div>
<footer>
  Generado por <span>NTTDATA IBM TWX Reverse Engineering Suite v1.0.0</span>
  &nbsp;·&nbsp; Cross-Model Pattern Analyzer
  &nbsp;·&nbsp; <span>{_esc(now)}</span>
  &nbsp;·&nbsp; <span>NTT DATA EMEAL · llopezdo@emeal.nttdata.com</span>
</footer>
<script>
// Highlight active nav link on scroll
const secs = document.querySelectorAll('.section[id]');
const links = document.querySelectorAll('nav a');
window.addEventListener('scroll', () => {{
  let cur = '';
  secs.forEach(s => {{ if (window.scrollY >= s.offsetTop - 80) cur = s.id; }});
  links.forEach(a => {{
    a.classList.toggle('active', a.getAttribute('href') === '#' + cur);
  }});
}}, {{passive: true}});
</script>
</body></html>
"""


# ─────────────────────────────────────────────────────────────────────────────
# Section 1 — Executive Summary
# ─────────────────────────────────────────────────────────────────────────────

def _section_summary(report: "CrossModelReport") -> str:
    s = report.stats
    total    = s.get("total_distinct_bo_names", 0)
    shared   = s.get("shared_across_files", 0)
    identical= s.get("shared_identical_definition", 0)
    divergent= s.get("shared_divergent_definition", 0)
    unique_n = s.get("unique_to_single_file", 0)
    clusters = s.get("structural_clusters_found", 0)
    n_files  = s.get("twx_files_analyzed", 0)

    pct_shared   = round(shared   / total * 100) if total else 0
    pct_identical= round(identical/ total * 100) if total else 0
    pct_unique   = round(unique_n / total * 100) if total else 0

    cards = [
        ("stat-n blue",  "blue",  n_files,   "Ficheros TWX analizados"),
        ("stat-n teal",  "teal",  total,     "Business Objects distintos"),
        ("stat-n green", "green", shared,    "BOs compartidos (≥2 TWX)"),
        ("stat-n amber", "amber", divergent, "BOs con definición divergente"),
        ("stat-n purple","purple",clusters,  "Clusters estructurales"),
        ("stat-n red",   "red",   unique_n,  "BOs únicos (1 solo TWX)"),
    ]
    cards_html = "".join(
        f'<div class="stat-card {color}">'
        f'<div class="{cls}">{n}</div>'
        f'<div class="stat-l">{l}</div>'
        f'</div>'
        for cls, color, n, l in cards
    )

    # File list
    files_html = "".join(
        f'<div class="file-item">'
        f'<span class="file-icon">📦</span>'
        f'<div><div class="file-name">{_esc(p.split("/")[-1].split(chr(92))[-1])}</div>'
        f'<div class="file-path">{_esc(p)}</div></div>'
        f'</div>'
        for p in report.twx_files
    )

    # Reusability bar chart
    bars = [
        ("Reutilizables (idénticos)",   identical, total, "#16a34a"),
        ("Reutilizables (divergentes)", divergent, total, "#d97706"),
        ("Únicos por fichero",          unique_n,  total, "#64748b"),
        ("Clusters estructurales",      clusters,  max(total, 1), "#7c3aed"),
    ]
    bars_html = "".join(
        f'<div class="bar-row">'
        f'<div class="bar-label">{lbl}</div>'
        f'<div class="bar-track"><div class="bar-fill" style="width:{round(v/t*100) if t else 0}%;background:{c}"></div></div>'
        f'<div class="bar-pct" style="color:{c}">{round(v/t*100) if t else 0}%</div>'
        f'</div>'
        for lbl, v, t, c in bars
    )

    # Insight alert
    if pct_shared >= 60:
        insight = ("success",
            "🎯 <strong>Alta reutilización detectada.</strong> "
            f"El {pct_shared}% de los Business Objects es compartido entre ficheros. "
            "Candidatos claros para un toolkit de datos común.")
    elif pct_shared >= 30:
        insight = ("info",
            "ℹ️ <strong>Reutilización moderada.</strong> "
            f"El {pct_shared}% de los BOs aparece en múltiples TWX. "
            "Hay oportunidades de consolidación.")
    else:
        insight = ("warn",
            "⚠️ <strong>Baja reutilización.</strong> "
            f"Solo el {pct_shared}% de los BOs se comparte. "
            "Los modelos de datos son mayoritariamente independientes.")

    return f"""
<section class="section" id="s1">
  <div class="sh">
    <span class="icon">📊</span>
    <h2>1. Resumen Ejecutivo</h2>
    <span class="cnt">{total} Business Objects · {n_files} ficheros</span>
  </div>
  <div class="sb">
    <div class="alert {insight[0]}">
      <span class="alert-icon">{'🎯' if insight[0]=='success' else 'ℹ️' if insight[0]=='info' else '⚠️'}</span>
      <div>{insight[1]}</div>
    </div>
    <div class="stats-grid">{cards_html}</div>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px">
      <div class="score-bar">
        <h4>📈 Distribución del modelo de datos</h4>
        {bars_html}
      </div>
      <div>
        <h4 style="font-size:12px;font-weight:700;color:var(--navy);margin-bottom:10px">
          📦 Ficheros analizados
        </h4>
        <div class="file-list">{files_html}</div>
      </div>
    </div>
  </div>
</section>
"""


# ─────────────────────────────────────────────────────────────────────────────
# Section 2 — Shared / Reusable BOs
# ─────────────────────────────────────────────────────────────────────────────

def _section_shared(report: "CrossModelReport") -> str:
    shared = report.shared
    if not shared:
        return f"""
<section class="section" id="s2">
  <div class="sh"><span class="icon">♻️</span><h2>2. Business Objects Compartidos</h2>
  <span class="cnt">0</span></div>
  <div class="sb">
    <div class="alert info">
      <span class="alert-icon">ℹ️</span>
      <div>No se encontraron Business Objects con el mismo nombre en múltiples ficheros TWX.</div>
    </div>
  </div>
</section>"""

    identical = [s for s in shared if s.is_identical]
    divergent = [s for s in shared if not s.is_identical]

    def _bo_card(s) -> str:
        kind = "identical" if s.is_identical else "divergent"
        badge = _badge("✅ Idéntico — reutilizable", "green") if s.is_identical \
                else _badge("⚠️ Divergente — revisar", "amber")
        # F3 category badge
        f3_cat = getattr(s, "f3_category", "dto")
        f3_colors = {"domain_entity": "teal", "catalog": "purple", "dto": "gray"}
        f3_labels = {
            "domain_entity": "F3: Record Type",
            "catalog":       "F3: Catálogo",
            "dto":           "F3: CDT/variable",
        }
        f3_badge = _badge(f3_labels.get(f3_cat, f3_cat), f3_colors.get(f3_cat, "gray"))
        files_str = " · ".join(
            f'<code>{_esc(a.twx_name)}</code>' for a in s.appearances
        )

        # Build comparison table across files
        # Collect all field names across all appearances
        all_field_names: list[str] = []
        seen: set[str] = set()
        for a in s.appearances:
            for f in a.bo.fields:
                if f.name not in seen:
                    all_field_names.append(f.name)
                    seen.add(f.name)

        if all_field_names:
            # Header: Field | TWX1 | TWX2 | ...
            th_files = "".join(
                f'<th style="min-width:120px">{_esc(a.twx_name)}</th>'
                for a in s.appearances
            )
            table_rows = ""
            for fname in all_field_names:
                cells = ""
                in_all = True
                diverges = False
                types_seen: set[str] = set()
                for a in s.appearances:
                    field_map = {f.name: f for f in a.bo.fields}
                    if fname in field_map:
                        f = field_map[fname]
                        types_seen.add(f.type_ref)
                        lst = "[]" if f.is_list else ""
                        req = " *" if f.required else ""
                        cells += f'<td><code>{_esc(f.type_ref)}{lst}</code>{req}</td>'
                    else:
                        in_all = False
                        cells += '<td style="color:#dc2626;font-style:italic">— ausente —</td>'
                diverges = len(types_seen) > 1 or not in_all
                row_style = ' style="background:#fef9ec"' if diverges else ''
                mark = ' <span style="color:#d97706">⚠</span>' if diverges else ''
                table_rows += (
                    f'<tr{row_style}>'
                    f'<td><code>{_esc(fname)}</code>{mark}</td>'
                    f'{cells}</tr>'
                )

            comparison = (
                f'<div class="tbl-wrap" style="margin-top:10px">'
                f'<table><tr><th>Campo</th>{th_files}</tr>{table_rows}</table>'
                f'</div>'
            )
        else:
            comparison = '<p style="color:var(--muted);font-size:11px;margin-top:8px">Sin campos declarados.</p>'

        divergent_fields_html = ""
        if s.divergent_fields:
            pills = " ".join(_badge(f, "amber") for f in s.divergent_fields)
            divergent_fields_html = (
                f'<div style="margin-top:8px">'
                f'<span style="font-size:11px;color:var(--tx-s)">Campos divergentes: </span>'
                f'{pills}</div>'
            )

        return f"""
<div class="card {kind}">
  <div class="card-header">
    <span style="font-size:16px">{'✅' if s.is_identical else '⚠️'}</span>
    <h4><code>{_esc(s.name)}</code></h4>
    {badge}
    {f3_badge}
    <span style="font-size:11px;color:var(--muted);margin-left:8px">
      {len(s.appearances)} ficheros
    </span>
  </div>
  <div style="font-size:11px;color:var(--tx-s);margin-bottom:6px">
    Presente en: {files_str}
  </div>
  {divergent_fields_html}
  <details {'open' if len(all_field_names) <= 8 else ''}>
    <summary>📋 Ver comparación de campos ({len(all_field_names)} campos)</summary>
    <div class="details-body">{comparison}</div>
  </details>
</div>"""

    identical_html = "".join(_bo_card(s) for s in identical) if identical else \
        '<p style="color:var(--muted);font-style:italic;font-size:12px">Ninguno.</p>'
    divergent_html = "".join(_bo_card(s) for s in divergent) if divergent else \
        '<p style="color:var(--muted);font-style:italic;font-size:12px">Ninguno.</p>'

    return f"""
<section class="section" id="s2">
  <div class="sh">
    <span class="icon">♻️</span>
    <h2>2. Business Objects Compartidos / Reutilizables</h2>
    <span class="cnt">{len(shared)} BOs · {len(identical)} idénticos · {len(divergent)} divergentes</span>
  </div>
  <div class="sb">
    <div class="alert success">
      <span class="alert-icon">✅</span>
      <div>
        <strong>Idénticos</strong> — definición 100% igual en todos los ficheros.
        Pueden extraerse a un toolkit compartido sin modificación.<br>
        <strong>Divergentes</strong> — el mismo nombre tiene campos diferentes según el fichero.
        Requieren revisión antes de consolidar.
      </div>
    </div>

    <h3 style="font-size:13px;color:var(--green);font-weight:700;margin:14px 0 10px">
      ✅ Reutilizables sin cambios ({len(identical)})
    </h3>
    {identical_html}

    <hr class="divider">

    <h3 style="font-size:13px;color:var(--amber);font-weight:700;margin:14px 0 10px">
      ⚠️ Compartidos con divergencias ({len(divergent)})
    </h3>
    {divergent_html}
  </div>
</section>
"""


# ─────────────────────────────────────────────────────────────────────────────
# Section 3 — Structural Clusters
# ─────────────────────────────────────────────────────────────────────────────

def _section_clusters(report: "CrossModelReport") -> str:
    clusters = report.structural_clusters
    if not clusters:
        return f"""
<section class="section" id="s3">
  <div class="sh"><span class="icon">🔗</span><h2>3. Clusters Estructurales</h2>
  <span class="cnt">0</span></div>
  <div class="sb">
    <div class="alert info">
      <span class="alert-icon">ℹ️</span>
      <div>No se detectaron Business Objects con estructura de campos idéntica y nombres distintos.</div>
    </div>
  </div>
</section>"""

    clusters_html = ""
    for c in clusters:
        rows = "".join(
            f'<tr><td><code>{_esc(m["twx"])}</code></td>'
            f'<td><code>{_esc(m["bo_name"])}</code></td>'
            f'<td style="color:var(--muted);font-size:11px">{_esc(m.get("description") or "—")}</td></tr>'
            for m in c.members
        )
        distinct_names = len({m["bo_name"] for m in c.members})
        distinct_files = len({m["twx"]    for m in c.members})
        clusters_html += f"""
<div class="cluster-card">
  <div class="cluster-header">
    <div class="cluster-id">{c.cluster_id}</div>
    <div style="flex:1">
      <div style="font-size:12px;font-weight:700">
        Cluster #{c.cluster_id} &nbsp;·&nbsp;
        {_badge(f'{distinct_names} nombres distintos', 'blue')}
        {_badge(f'{distinct_files} ficheros', 'teal')}
      </div>
      <div class="cluster-sig">{_esc(c.field_signature)}</div>
    </div>
  </div>
  <div style="padding:14px">
    <div class="alert warn" style="margin-bottom:12px">
      <span class="alert-icon">🔗</span>
      <div>Estos BOs tienen <strong>exactamente la misma firma de campos</strong> pero nombres distintos.
      Son candidatos para unificarse en un único tipo reutilizable.</div>
    </div>
    <div class="tbl-wrap">
      <table>
        <tr><th>Fichero TWX</th><th>Nombre del BO</th><th>Descripción</th></tr>
        {rows}
      </table>
    </div>
  </div>
</div>"""

    return f"""
<section class="section" id="s3">
  <div class="sh">
    <span class="icon">🔗</span>
    <h2>3. Clusters Estructurales</h2>
    <span class="cnt">{len(clusters)} clusters detectados</span>
  </div>
  <div class="sb">
    <div class="alert info">
      <span class="alert-icon">🔗</span>
      <div>
        Los clusters agrupan Business Objects con <strong>diferentes nombres pero idéntica estructura
        de campos</strong>. Son el resultado de desarrollo paralelo o de nomenclaturas inconsistentes
        y representan las mejores oportunidades de consolidación en un modelo de datos compartido.
      </div>
    </div>
    {clusters_html}
  </div>
</section>
"""


# ─────────────────────────────────────────────────────────────────────────────
# Section 4 — Unique BOs per TWX
# ─────────────────────────────────────────────────────────────────────────────

def _section_unique(report: "CrossModelReport") -> str:
    unique = report.unique
    total_unique = sum(len(v) for v in unique.values())

    blocks = ""
    for twx_name, bo_names in unique.items():
        if bo_names:
            pills = "".join(
                f'<div class="unique-pill">{_esc(n)}</div>'
                for n in sorted(bo_names)
            )
            content = f'<div class="unique-grid">{pills}</div>'
        else:
            content = '<p style="color:var(--muted);font-style:italic;font-size:12px">Todos los BOs están compartidos con al menos un otro fichero.</p>'

        blocks += f"""
<details {'open' if len(bo_names) <= 10 else ''}>
  <summary>
    <span style="flex:1"><code>{_esc(twx_name)}</code></span>
    {_badge(str(len(bo_names)) + ' BOs únicos', 'gray')}
  </summary>
  <div class="details-body">{content}</div>
</details>"""

    return f"""
<section class="section" id="s4">
  <div class="sh">
    <span class="icon">🔒</span>
    <h2>4. Business Objects Únicos por Fichero</h2>
    <span class="cnt">{total_unique} BOs · exclusivos de su TWX</span>
  </div>
  <div class="sb">
    <div class="alert info">
      <span class="alert-icon">🔒</span>
      <div>Estos Business Objects aparecen <strong>solo en un fichero TWX</strong>.
      Son parte del dominio específico de esa aplicación y no candidatos directos
      a reutilización — a menos que la aplicación sea la referencia del modelo.</div>
    </div>
    {blocks}
  </div>
</section>
"""


# ─────────────────────────────────────────────────────────────────────────────
# Section 5 — Full model per TWX
# ─────────────────────────────────────────────────────────────────────────────

def _section_full_model(report: "CrossModelReport") -> str:
    per_twx = report.per_twx
    shared_names = {s.name for s in report.shared}
    # Build F3 category lookup from shared BOs
    f3_category_map: dict[str, str] = {}
    for s in report.shared:
        f3_category_map[s.name] = getattr(s, "f3_category", "dto")

    F3_LABELS = {"domain_entity": "F3: Record Type", "catalog": "F3: Catálogo", "dto": "F3: CDT"}
    F3_COLORS = {"domain_entity": "teal", "catalog": "purple", "dto": "gray"}

    twx_blocks = ""
    for twx_name, bos in per_twx.items():
        if not bos:
            bo_content = '<p style="color:var(--muted);font-style:italic">Sin Business Objects.</p>'
        else:
            bo_cards = ""
            for bo in bos:
                name = bo.get("name", "?")
                is_shared = name in shared_names
                shared_badge = _badge("compartido", "green") if is_shared else _badge("único", "gray")
                f3_cat = f3_category_map.get(name, "dto")
                f3_badge = _badge(F3_LABELS[f3_cat], F3_COLORS[f3_cat])
                fields = bo.get("fields", [])
                parent_html = (
                    f'<div style="font-size:11px;color:var(--muted);margin-bottom:6px">'
                    f'Hereda de: <code>{_esc(bo["parent"])}</code></div>'
                    if bo.get("parent") else ""
                )
                if fields:
                    field_rows = "".join(
                        f'<tr><td><code>{_esc(f.get("name","?"))}</code></td>'
                        f'<td><code>{_esc(f.get("type","?"))}</code>'
                        f'{"<span style='color:#7c3aed'>[]</span>" if f.get("is_list") else ""}</td>'
                        f'<td>{"✓" if f.get("required") else ""}</td>'
                        f'<td style="color:var(--muted)">{_esc(str(f.get("default") or ""))}</td>'
                        f'<td style="color:var(--muted);font-size:11px">{_esc(str(f.get("description") or ""))}</td></tr>'
                        for f in fields
                    )
                    field_table = (
                        f'<div class="tbl-wrap">'
                        f'<table><tr><th>Campo</th><th>Tipo</th>'
                        f'<th>Req</th><th>Default</th><th>Descripción</th></tr>'
                        f'{field_rows}</table></div>'
                    )
                else:
                    field_table = '<p style="color:var(--muted);font-style:italic;font-size:11px">Sin campos declarados.</p>'

                bo_cards += f"""
<details>
  <summary>
    <span style="flex:1"><strong>{_esc(name)}</strong></span>
    {shared_badge}
    {f3_badge}
    {_badge(str(len(fields)) + ' campos', 'blue')}
  </summary>
  <div class="details-body">
    {parent_html}
    {field_table}
  </div>
</details>"""

            bo_content = bo_cards

        twx_blocks += f"""
<details>
  <summary>
    <span style="flex:1;font-size:13px">
      📦 <strong>{_esc(twx_name)}</strong>
    </span>
    {_badge(str(len(bos)) + ' Business Objects', 'teal')}
  </summary>
  <div class="details-body">
    {bo_content}
  </div>
</details>"""

    return f"""
<section class="section" id="s5">
  <div class="sh">
    <span class="icon">📐</span>
    <h2>5. Modelo de Datos Completo por Fichero</h2>
    <span class="cnt">{len(per_twx)} ficheros TWX</span>
  </div>
  <div class="sb">
    <div class="alert info">
      <span class="alert-icon">📐</span>
      <div>Inventario completo de todos los Business Objects extraídos de cada fichero TWX.
      Los marcados en <strong style="color:var(--green)">verde</strong> aparecen en más de un fichero.</div>
    </div>
    {twx_blocks}
  </div>
</section>
"""


# ─────────────────────────────────────────────────────────────────────────────
# Main entry point
# ─────────────────────────────────────────────────────────────────────────────

def generate_cross_model_html(report: "CrossModelReport") -> str:
    """Generates the full HTML report for a CrossModelReport."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    return (
        _page_open(report, now)
        + _section_summary(report)
        + _section_shared(report)
        + _section_clusters(report)
        + _section_unique(report)
        + _section_full_model(report)
        + _page_close(now)
    )
