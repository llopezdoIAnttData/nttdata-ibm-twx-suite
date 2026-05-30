"""
IS Parameters HTML Report Generator
=====================================
Generates a navigable HTML report showing all Integration Services (WebServices)
from IBM BPM TWX files with their request/response parameters.

Based on the original is_parameters_report.html generated on 26/05/2026 for the
Profuturo project after the RETRO APPIAN session.

The HTML includes:
  - Async Tipo 2 section: processes that are callback receivers → NOV_INSTANCE_MANAGEMENT
  - IS por módulo: collapsible per-module view with each IS and its operations
  - VS Code-style XML syntax highlighting for processParameter elements
"""

from __future__ import annotations

import html as _html
import re
from datetime import date as _date
from typing import Optional

from .web_service_extractor import BPDVarInfo, OperationInfo, WSInfo


# ── NCI_BR column hints: BPD variable name (lowercase) → NCI_BR column ───────
# Based on Profuturo "NCI_BR Proceso Redencion" table (and similar modules).
# These hints annotate REQUEST params so Appian devs know where to read values.
_NCI_BR_HINTS: dict[str, str] = {
    "folio":            "folio_case",
    "archivo":          "id_archivo",
    "idarchivo":        "id_archivo",
    "idproceso":        "id_proceso",
    "idsubproceso":     "id_subproceso",
    "idsubetapa":       "substage",
    "idetapa":          "stage",
    "esproceso":        "reprocesoflag",
    "esenvio":          "Envio",
    "exitocargo":       "Cargo",
    "ismocargo":        "Cargo",
    "exitoabono":       "Abono",
    "descproceso":      "proceso",
    "descsubproceso":   "subproceso",
    "usuario":          "createdBy",
    "id_instance":      "id_instance",
}


# ── Module color palette (cycles if > 14 modules) ────────────────────────────
_COLORS = [
    "#b91c1c", "#b45309", "#047857", "#1d4ed8", "#7c3aed",
    "#c026d3", "#0369a1", "#0f766e", "#1e40af", "#6b21a8",
    "#be123c", "#0891b2", "#14532d", "#78350f",
]


def _esc(text: str) -> str:
    return _html.escape(str(text), quote=True)


def _highlight_xml(raw_xml: str) -> str:
    """
    Apply VS Code-dark-theme inline-style syntax highlighting to an XML string.
    Converts a raw XML fragment to colored <span> elements.
    """
    import xml.etree.ElementTree as ET

    # Try to pretty-print via ET
    try:
        el = ET.fromstring(raw_xml)
        lines = _pretty_xml_el(el, indent=0)
    except Exception:
        lines = [_html.escape(raw_xml)]

    return "\n".join(lines)


def _pretty_xml_el(el, indent: int) -> list[str]:
    """Recursively render an XML element as VS Code-highlighted HTML lines."""
    pad = "  " * indent
    tag = el.tag.split("}")[-1]  # strip namespace

    # Attributes
    attrs_html = ""
    for k, v in el.attrib.items():
        k_local = k.split("}")[-1]
        attrs_html += (
            f' <span style="color:#9cdcfe">{_esc(k_local)}</span>'
            f'<span style="color:#808080">=</span>'
            f'<span style="color:#ce9178">&quot;{_esc(v)}&quot;</span>'
        )

    open_tag = (
        f'{pad}<span style="color:#808080">&lt;</span>'
        f'<span style="color:#4ec9b0">{_esc(tag)}</span>'
        f'{attrs_html}'
    )

    children = list(el)
    text = (el.text or "").strip()

    if not children and not text:
        # Self-closing or empty
        lines = [open_tag + f'<span style="color:#808080">/&gt;</span>']
    elif not children:
        # Inline text content
        line = (
            open_tag
            + f'<span style="color:#808080">&gt;</span>'
            + f'<span style="color:#dcdcaa">{_esc(text)}</span>'
            + f'<span style="color:#808080">&lt;/</span>'
            + f'<span style="color:#4ec9b0">{_esc(tag)}</span>'
            + f'<span style="color:#808080">&gt;</span>'
        )
        lines = [line]
    else:
        lines = [open_tag + f'<span style="color:#808080">&gt;</span>']
        for child in children:
            lines.extend(_pretty_xml_el(child, indent + 1))
        lines.append(
            f'{pad}<span style="color:#808080">&lt;/</span>'
            f'<span style="color:#4ec9b0">{_esc(tag)}</span>'
            f'<span style="color:#808080">&gt;</span>'
        )

    return lines


def _param_table(params, is_response: bool = False) -> str:
    """Render a clean parameter table: Name | Type | [NCI_BR hint]."""
    if not params:
        if is_response:
            return '<div class="no-is">Sin parámetros definidos — <span class="map-badge">map()</span></div>'
        return '<div class="no-is">Sin parámetros definidos</div>'

    rows = ""
    for p in params:
        arr_badge = (
            '<span class="arr-badge">[ ]</span>' if p.is_array else ""
        )
        if is_response:
            type_display = (
                f'<span class="p-type-dim">{_esc(p.type_name)}</span>'
                f'<span class="map-badge-sm">map()</span>'
                f'{arr_badge}'
            )
            nci_cell = ""
        else:
            type_color = "#7c3aed" if p.is_array else "#0891b2"
            type_display = (
                f'<span class="p-type" style="color:{type_color}">'
                f'{_esc(p.type_name)}</span>{arr_badge}'
            )
            hint = _NCI_BR_HINTS.get(p.name.lower(), "")
            nci_cell = (
                f'<td class="p-nci" title="Lee de NCI_BR.{_esc(hint)}">'
                f'<span class="nci-hint">📋 {_esc(hint)}</span></td>'
            ) if hint else "<td></td>"

        rows += (
            f'<tr>'
            f'<td class="p-name">{_esc(p.name)}</td>'
            f'<td>{type_display}</td>'
            f'{nci_cell}'
            f'</tr>\n'
        )

    if is_response:
        header = "<tr><th>Parámetro</th><th>Tipo IBM BPM (ref.)</th></tr>"
    else:
        header = "<tr><th>Parámetro</th><th>Tipo</th><th>NCI_BR</th></tr>"

    return f"""<table class="param-table">
<thead>{header}</thead>
<tbody>{rows}</tbody>
</table>"""


def _op_params_html(op: OperationInfo) -> str:
    """Render a 2-column REQUEST/RESPONSE grid for one operation."""
    n_in = len(op.inputs)
    n_out = len(op.outputs)
    process_name = _esc(op.process_name) if op.process_name else "<em>N/A</em>"

    # Brief param names shown in the summary line
    in_names = " · ".join(p.name for p in op.inputs[:4])
    if len(op.inputs) > 4:
        in_names += f" +{len(op.inputs)-4}"

    return f"""<details class="op-details">
<summary class="op-summary">
  <span class="op-name-text">▶ {_esc(op.name)}</span>
  <span style="font-size:11px;color:#94a3b8;font-style:italic">{_esc(in_names)}</span>
</summary>
<div class="op-content">
  <div style="font-size:11px;color:#94a3b8;margin-bottom:12px">
    Proceso IBM BPM: <strong style="color:#475569">{process_name}</strong>
  </div>
  <div class="req-res-grid">
    <div class="req-res-col">
      <div class="col-header col-req">
        <span>📥</span>
        <span class="dir-label dir-in">REQUEST</span>
        <span class="param-count">{n_in} param.</span>
        <span class="nci-legend">📋 = columna NCI_BR</span>
      </div>
      <div class="col-body">{_param_table(op.inputs, is_response=False)}</div>
    </div>
    <div class="req-res-col">
      <div class="col-header col-res">
        <span>📤</span>
        <span class="dir-label dir-out">RESPONSE</span>
        <span class="param-count">{n_out} param.</span>
        <span class="map-badge-header">→ map() en Appian</span>
      </div>
      <div class="col-body">{_param_table(op.outputs, is_response=True)}</div>
    </div>
  </div>
</div>
</details>"""


def _bpd_vars_section_html(bpd_vars: list[BPDVarInfo]) -> str:
    """Render the BPD Flow Variables section with NCI_BR coverage analysis."""
    if not bpd_vars:
        return ""

    covered = [v for v in bpd_vars if v.in_nci_br]
    candidates = [v for v in bpd_vars if not v.in_nci_br]
    # Candidates: IN vars (used to build requests) by priority
    in_candidates = [v for v in candidates if "IN" in v.direction]
    out_candidates = [v for v in candidates if v.direction == "OUT"]

    def _var_row(v: BPDVarInfo, bg: str = "") -> str:
        dir_badge = (
            '<span style="background:#dbeafe;color:#1e40af;padding:1px 6px;'
            'border-radius:5px;font-size:10px;font-weight:700">IN</span>'
            if "IN" in v.direction else
            '<span style="background:#f5f3ff;color:#6d28d9;padding:1px 6px;'
            'border-radius:5px;font-size:10px;font-weight:700">OUT</span>'
        )
        freq_color = "#dc2626" if v.frequency >= 8 else ("#d97706" if v.frequency >= 3 else "#64748b")
        bg_style = f'style="background:{bg}"' if bg else ""
        bpd_tip = " · ".join(v.bpd_names[:3]) + (f" +{len(v.bpd_names)-3}" if len(v.bpd_names) > 3 else "")
        return (
            f'<tr {bg_style}>'
            f'<td class="p-name" title="{_esc(bpd_tip)}">{_esc(v.name)}</td>'
            f'<td style="font-size:11px;color:#0891b2;font-family:monospace">{_esc(v.type_name)}</td>'
            f'<td style="text-align:center">{dir_badge}</td>'
            f'<td style="text-align:center;font-weight:800;color:{freq_color}">{v.frequency}</td>'
            f'</tr>\n'
        )

    # Build covered table
    covered_rows = "".join(_var_row(v, "#f0fdf4") for v in covered)
    # Build IN candidates (priority for NCI_BR)
    in_rows = "".join(_var_row(v) for v in in_candidates)
    # Build OUT candidates (usually don't need to be in NCI_BR)
    out_rows = "".join(_var_row(v, "#fafbfc") for v in out_candidates)

    def _table(rows: str, header_extra: str = "") -> str:
        return f"""<table class="param-table" style="margin-bottom:16px">
<thead><tr><th>Variable BPD</th><th>Tipo IBM</th><th>Dir.</th>
<th title="Cantidad de SPs que la usan">Freq.</th>{header_extra}</tr></thead>
<tbody>{rows}</tbody></table>"""

    return f"""<div class="section" id="bpd-vars">
  <div class="sec-title">
    <div class="icon">🧩</div>
    <h2>Variables del Flujo BPD — Cobertura NCI_BR</h2>
  </div>
  <p class="sec-desc">Variables de proceso (BPD) extraídas del TWX Redención de Bono.
  Las <strong>variables IN</strong> son las que Appian necesita tener disponibles en el Record Type
  para construir los REQUEST de cada IS. <em>Freq.</em> = número de sub-procesos que la usan.</p>

  <div style="display:grid;grid-template-columns:1fr 1fr;gap:20px;margin-bottom:24px">
    <div>
      <div style="font-weight:800;color:#065f46;margin-bottom:8px;font-size:13px">
        ✅ Ya en NCI_BR ({len(covered)} variables)
      </div>
      {_table(covered_rows)}
    </div>
    <div>
      <div style="font-weight:800;color:#92400e;margin-bottom:8px;font-size:13px">
        ⚠️ Candidatos IN nuevos — revisar si agregar a NCI_BR ({len(in_candidates)})
      </div>
      {_table(in_rows)}
      <div style="font-weight:800;color:#64748b;margin-bottom:8px;font-size:13px">
        📤 Variables de salida — no requieren NCI_BR ({len(out_candidates)})
      </div>
      {_table(out_rows)}
    </div>
  </div>

  <div style="background:#fffbeb;border:1px solid #fde68a;border-radius:12px;
              padding:16px 20px;font-size:13px;line-height:1.8">
    <strong>💡 Recomendación:</strong>
    Considerar agregar a la tabla NCI_BR las variables IN con Freq ≥ 3:
    <code style="background:#fef3c7;padding:1px 6px;border-radius:4px">diaHabilAnterior</code>
    <code style="background:#fef3c7;padding:1px 6px;border-radius:4px">fechaSeleccionada</code>
    <code style="background:#fef3c7;padding:1px 6px;border-radius:4px">fecha</code>
    <code style="background:#fef3c7;padding:1px 6px;border-radius:4px">isMovCargo</code>
    <code style="background:#fef3c7;padding:1px 6px;border-radius:4px">isGeneroArchivoRespuesta</code>
    <code style="background:#fef3c7;padding:1px 6px;border-radius:4px">esRechazoCargos</code>
    <code style="background:#fef3c7;padding:1px 6px;border-radius:4px">accion</code>
  </div>
</div>"""


def _ws_html(ws: WSInfo) -> str:
    """Render one WebService collapsible block."""
    n_ops = len(ws.operations)
    binding_label = ws.binding.upper() if ws.binding else "SOAP"
    ops_html = "\n".join(_op_params_html(op) for op in ws.operations)
    return f"""<details class="svc-details">
<summary class="svc-summary">
  <span style="font-size:18px">🔌</span>
  <span class="svc-name">{_esc(ws.name)}</span>
  <span class="bind-badge" style="background:#0891b2;color:#fff">{_esc(binding_label)}</span>
  <span style="font-size:12px;color:#64748b">{n_ops} ops</span>
  <span class="svc-toggle"></span>
</summary>
{ops_html}
</details>"""


def _module_html(module_name: str, color: str, ws_list: list[WSInfo]) -> str:
    """Render one module collapsible block."""
    n_is = len(ws_list)
    n_ops = sum(len(ws.operations) for ws in ws_list)
    ws_blocks = "\n".join(_ws_html(ws) for ws in ws_list)
    return f"""<details class="mod-details">
<summary class="mod-summary" style="border-left-color:{color}">
  <span class="mod-badge" style="background:{color}">{_esc(module_name)}</span>
  <span style="font-size:12px;color:#64748b">{n_is} IS · {n_ops} operaciones</span>
  <span class="mod-toggle"></span>
</summary>
<div class="mod-body">
{ws_blocks}
</div>
</details>"""


def _async_grid_html(async_names: list[str]) -> str:
    cards = ""
    for name in async_names:
        cards += f"""<div class="async-card">
  <div style="font-size:13px;font-weight:800;color:#5b21b6;margin-bottom:6px">⚡ {_esc(name)}</div>
  <div style="font-size:11px;color:#64748b">
    <span style="background:#ede9fe;color:#5b21b6;padding:1px 7px;border-radius:8px;
                 font-size:11px;font-weight:700">Async Tipo 2</span>&nbsp;→ NOV_INSTANCE_MANAGEMENT
  </div>
</div>"""
    return cards


# ── CSS ───────────────────────────────────────────────────────────────────────

_CSS = """
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:'Segoe UI',system-ui,sans-serif;background:#f0f4f8;color:#1e293b;font-size:14px}
header{background:linear-gradient(135deg,#001a4d 0%,#003087 60%,#0055aa 100%);color:#fff;
       padding:40px 48px 32px;position:relative;overflow:hidden}
header::after{content:'';position:absolute;top:-80px;right:-80px;width:320px;height:320px;
              background:rgba(255,255,255,.06);border-radius:50%}
.h-badge{background:#0891b2;color:#fff;font-size:11px;font-weight:700;letter-spacing:1px;
         padding:4px 14px;border-radius:20px;margin-bottom:14px;display:inline-block;text-transform:uppercase}
header h1{font-size:28px;font-weight:800;line-height:1.2;margin-bottom:6px}
header h1 span{color:#7eb8ff}
header p{font-size:13px;opacity:.75;max-width:700px;line-height:1.7;margin-bottom:20px}
.h-meta{display:flex;gap:12px;flex-wrap:wrap}
.h-meta-item{background:rgba(255,255,255,.1);border:1px solid rgba(255,255,255,.2);
             padding:7px 14px;border-radius:8px;font-size:12px}
.h-meta-item strong{display:block;color:#7eb8ff;font-size:13px}
nav{background:#fff;border-bottom:2px solid #dde3ea;padding:0 40px;display:flex;gap:0;
    overflow-x:auto;position:sticky;top:0;z-index:100;box-shadow:0 2px 8px rgba(0,0,0,.06)}
nav a{padding:13px 16px;font-size:13px;font-weight:600;color:#64748b;
      border-bottom:3px solid transparent;white-space:nowrap;text-decoration:none}
nav a:hover{color:#003087;border-color:#003087}
.container{max-width:1300px;margin:0 auto;padding:32px 24px}
.section{margin-bottom:44px}
.sec-title{display:flex;align-items:center;gap:12px;margin-bottom:8px}
.sec-title .icon{width:40px;height:40px;border-radius:10px;background:#003087;color:#fff;
                 display:flex;align-items:center;justify-content:center;font-size:18px;flex-shrink:0}
.sec-title h2{font-size:21px;font-weight:800;color:#0f172a}
.sec-desc{color:#64748b;font-size:13px;line-height:1.7;margin-bottom:20px;max-width:900px}
.metric-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:14px;margin-bottom:24px}
.metric-card{background:#fff;border-radius:14px;padding:18px;text-align:center;
             box-shadow:0 2px 10px rgba(0,0,0,.07);border:1px solid #dde3ea}
.metric-card .num{font-size:40px;font-weight:800;line-height:1}
.metric-card .lbl{font-size:12px;color:#64748b;margin-top:4px;line-height:1.4}
.async-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:12px;margin-bottom:20px}
.async-card{background:#fff;border-radius:12px;padding:16px 18px;
            border-left:5px solid #7c3aed;box-shadow:0 2px 8px rgba(0,0,0,.06)}
details{margin-bottom:10px}
details summary{list-style:none;cursor:pointer;user-select:none}
details summary::-webkit-details-marker{display:none}
.mod-details{background:#fff;border-radius:14px;box-shadow:0 2px 10px rgba(0,0,0,.07);
             border:1px solid #dde3ea;overflow:hidden}
.mod-summary{padding:14px 20px;display:flex;align-items:center;gap:12px;
             border-left:6px solid #003087;transition:background .15s}
.mod-summary:hover{background:#f8fafc}
.mod-badge{color:#fff;padding:4px 14px;border-radius:20px;font-size:14px;font-weight:700;flex-shrink:0}
.mod-toggle{margin-left:auto;font-size:11px;color:#94a3b8;font-weight:600}
.mod-details[open] .mod-toggle::after{content:'▲ colapsar'}
.mod-details:not([open]) .mod-toggle::after{content:'▼ expandir'}
.mod-body{padding:12px 20px 20px}
.svc-details{border:1px solid #e2e8f0;border-radius:10px;margin-bottom:10px;overflow:hidden}
.svc-summary{background:#f8fafc;padding:10px 16px;display:flex;align-items:center;
             gap:10px;flex-wrap:wrap;transition:background .15s}
.svc-summary:hover{background:#eff6ff}
.svc-details[open] .svc-summary{border-bottom:1px solid #e2e8f0;background:#eff6ff}
.svc-name{font-size:13px;font-weight:800;color:#0f172a}
.bind-badge{padding:2px 9px;border-radius:10px;font-size:11px;font-weight:700}
.svc-toggle{margin-left:auto;font-size:11px;color:#94a3b8;font-weight:600}
.svc-details[open] .svc-toggle::after{content:'▲'}
.svc-details:not([open]) .svc-toggle::after{content:'▼'}
.op-details{border-bottom:1px solid #f1f5f9}
.op-details:last-child{border-bottom:none}
.op-summary{padding:9px 16px;display:flex;align-items:center;gap:8px;flex-wrap:wrap;transition:background .15s}
.op-summary:hover{background:#f8fafc}
.op-details[open] .op-summary{background:#f8fafc;border-bottom:1px solid #f1f5f9}
.op-name-text{font-size:13px;font-weight:700;color:#003087}
.op-content{padding:12px 20px 14px;background:#fafbfc}
.dir-label{font-size:11px;font-weight:800;letter-spacing:.5px;padding:2px 8px;
           border-radius:6px;display:inline-block;margin-bottom:6px;margin-right:4px}
.dir-in{background:#dbeafe;color:#1e40af}
.dir-out{background:#dcfce7;color:#14532d}
.no-is{background:#f8fafc;border-radius:8px;padding:12px 16px;color:#94a3b8;
       font-size:13px;font-style:italic;margin-top:12px}
.req-res-grid{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:12px}
.req-res-col{border:1px solid #e2e8f0;border-radius:10px;overflow:hidden}
.col-header{display:flex;align-items:center;gap:8px;padding:7px 14px;
            border-bottom:1px solid #e2e8f0;flex-wrap:wrap}
.col-req{background:#eff6ff}
.col-res{background:#f5f3ff}
.col-body{padding:8px 12px}
.param-count{font-size:10px;color:#94a3b8;margin-left:auto}
.map-badge-header{font-size:11px;font-weight:800;background:#7c3aed;color:#fff;
                  padding:2px 9px;border-radius:10px;margin-left:4px}
.map-badge{font-size:11px;font-weight:800;background:#ede9fe;color:#5b21b6;
           padding:1px 7px;border-radius:8px}
.map-badge-sm{font-size:10px;font-weight:700;background:#ede9fe;color:#7c3aed;
              padding:1px 6px;border-radius:6px;margin-left:5px}
.p-type-dim{font-family:'Cascadia Code','Consolas',monospace;font-weight:600;
            color:#94a3b8;font-size:11px}
.nci-legend{font-size:10px;color:#475569;margin-left:4px}
.nci-hint{font-size:10px;font-family:'Cascadia Code','Consolas',monospace;
          background:#ecfdf5;color:#065f46;padding:1px 6px;border-radius:6px;
          font-weight:700;white-space:nowrap}
.p-nci{white-space:nowrap}
.param-table{width:100%;border-collapse:collapse;font-size:12px}
.param-table th{text-align:left;font-size:11px;font-weight:700;color:#64748b;
                padding:4px 8px;border-bottom:1px solid #e2e8f0;text-transform:uppercase;
                letter-spacing:.5px}
.param-table td{padding:5px 8px;border-bottom:1px solid #f1f5f9;vertical-align:top}
.param-table tr:last-child td{border-bottom:none}
.p-name{font-family:'Cascadia Code','Consolas',monospace;color:#0f172a;font-weight:600}
.p-type{font-family:'Cascadia Code','Consolas',monospace;font-weight:700}
.arr-badge{font-size:10px;font-weight:800;color:#7c3aed;background:#ede9fe;
           padding:1px 5px;border-radius:4px;margin-left:5px}
footer{background:#0f172a;color:rgba(255,255,255,.5);text-align:center;
       padding:24px;font-size:12px;margin-top:48px}
footer strong{color:#fff}
"""


# ── Public API ────────────────────────────────────────────────────────────────

def generate_html(
    modules: list[tuple[str, list[WSInfo]]],
    async_tipo2: Optional[list[str]] = None,
    generated_date: Optional[str] = None,
    version: str = "1.1.0",
    bpd_vars: Optional[list[BPDVarInfo]] = None,
) -> str:
    """
    Generate the IS Parameters HTML report.

    Args:
        modules: list of (module_name, [WSInfo])  — in display order
        async_tipo2: list of process names that are Async Tipo 2 (optional)
        generated_date: date string, defaults to today
        version: suite version string
        bpd_vars: list of BPDVarInfo from BPDVariableExtractor (optional)
    """
    if async_tipo2 is None:
        async_tipo2 = []
    today = generated_date or _date.today().strftime("%d/%m/%Y")

    total_is = sum(len(ws_list) for _, ws_list in modules)
    total_ops = sum(
        sum(len(ws.operations) for ws in ws_list)
        for _, ws_list in modules
    )
    modules_with_is = sum(1 for _, ws_list in modules if ws_list)
    n_async = len(async_tipo2)
    n_modules = len(modules)

    # ── Async section ─────────────────────────────────────────────────────────
    async_section = ""
    if async_tipo2:
        retro_badge = (
            f'<div style="background:linear-gradient(135deg,#312e81,#4c1d95);color:#fff;'
            f'border-radius:14px;padding:18px 24px;margin-bottom:20px;font-size:13px;line-height:1.8">'
            f'<div style="background:#fbbf24;color:#1e1b4b;font-size:11px;font-weight:800;'
            f'padding:2px 10px;border-radius:14px;display:inline-block;margin-bottom:10px">'
            f'RETRO APPIAN {today}</div>'
            f'<p><strong style="color:#a5f3fc">IBM BPM:</strong> SP_async lanza WS → '
            f'espera callback UCA → respuesta via webService</p>'
            f'<p style="margin-top:6px"><strong style="color:#a5f3fc">Appian:</strong> '
            f'Integration Object async → escribe <code>NOV_INSTANCE_MANAGEMENT</code> → '
            f'Smart Service recibe respuesta → continúa proceso</p>'
            f'</div>'
        )
        async_section = f"""<div class="section" id="async">
  <div class="sec-title"><div class="icon">⚡</div><h2>Procesos Asíncronos Tipo 2 — Confirmados</h2></div>
  <p class="sec-desc">Estos {n_async} sub-procesos son <strong>asíncronos</strong>: lanzan una
  solicitud a un sistema externo y esperan respuesta vía callback UCA / webService.
  En Appian crean instancia en <code>NOV_INSTANCE_MANAGEMENT</code>.</p>
  {retro_badge}
  <div class="async-grid">{_async_grid_html(async_tipo2)}</div>
</div>"""

    # ── Modules section ───────────────────────────────────────────────────────
    modules_html = ""
    for i, (mod_name, ws_list) in enumerate(modules):
        color = _COLORS[i % len(_COLORS)]
        modules_html += _module_html(mod_name, color, ws_list) + "\n"

    metrics_html = f"""<div class="metric-grid">
  <div class="metric-card"><div class="num" style="color:#003087">{modules_with_is}</div>
    <div class="lbl">Módulos con IS</div></div>
  <div class="metric-card"><div class="num" style="color:#0891b2">{total_is}</div>
    <div class="lbl">Integration Services</div></div>
  <div class="metric-card"><div class="num" style="color:#7c3aed">{total_ops}</div>
    <div class="lbl">Operaciones total</div></div>
  <div class="metric-card"><div class="num" style="color:#16a34a">{n_async}</div>
    <div class="lbl">Async Tipo 2</div></div>
</div>"""

    appian_strategy_box = """<div style="background:linear-gradient(135deg,#312e81,#4c1d95);
  color:#fff;border-radius:14px;padding:18px 24px;margin-bottom:20px;font-size:13px;line-height:1.9">
  <div style="display:flex;align-items:center;gap:10px;margin-bottom:10px">
    <span style="font-size:18px">🧠</span>
    <strong style="font-size:14px">Estrategia Appian — Feedback RETRO 28/05/2026</strong>
  </div>
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px">
    <div style="background:rgba(255,255,255,.08);border-radius:10px;padding:12px 16px">
      <div style="color:#a5f3fc;font-weight:800;margin-bottom:6px">📥 REQUEST</div>
      <p>Los parámetros se leen del Record Type <strong>NCI_BR</strong> (tabla DB).
      Columna indicada con <span style="background:#ecfdf5;color:#065f46;
      padding:1px 6px;border-radius:6px;font-size:11px;font-weight:700">📋 campo</span>
      en la tabla de parámetros.</p>
    </div>
    <div style="background:rgba(255,255,255,.08);border-radius:10px;padding:12px 16px">
      <div style="color:#c4b5fd;font-weight:800;margin-bottom:6px">📤 RESPONSE → map()</div>
      <p>No se construyen CDTs complejos. Los responses se manejan como
      <code style="background:rgba(255,255,255,.15);padding:1px 6px;border-radius:4px">map()</code>
      para mayor flexibilidad ante cambios en servicios externos.</p>
    </div>
  </div>
</div>"""

    is_section = f"""<div class="section" id="is-modulos">
  <div class="sec-title"><div class="icon">🔌</div>
    <h2>Integration Services por Módulo — Parámetros</h2></div>
  <p class="sec-desc">WebServices y sus operaciones. REQUEST → columna NCI_BR de donde leer el valor.
  RESPONSE → <span class="map-badge">map()</span> en Appian (tipos IBM BPM visibles como referencia).</p>
  {appian_strategy_box}
  {metrics_html}
  {modules_html}
</div>"""

    nav_async = '<a href="#async">⚡ Async Tipo 2 ({n})</a>'.format(n=n_async) if async_tipo2 else ""
    bpd_section = _bpd_vars_section_html(bpd_vars) if bpd_vars else ""
    nav_bpd = '<a href="#bpd-vars">🧩 Variables BPD</a>' if bpd_vars else ""

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>IS Parameters — Profuturo Suite · {n_modules} módulos</title>
<style>{_CSS}</style>
</head>
<body>
<header>
  <div class="h-badge">🔌 Integration Services — Parámetros Request/Response</div>
  <h1>IS Parameters Report<br/><span>Profuturo Suite · {n_modules} Módulos IBM BPM</span></h1>
  <p>Parámetros de Request/Response por IS. REQUEST muestra la columna NCI_BR de donde leer el valor.
  RESPONSE se maneja como <code>map()</code> en Appian (flexible ante cambios en servicios).</p>
  <div class="h-meta">
    <div class="h-meta-item"><strong>Generado</strong>{today}</div>
    <div class="h-meta-item"><strong>Módulos analizados</strong>{n_modules}</div>
    <div class="h-meta-item"><strong>IS encontrados</strong>{total_is}</div>
    <div class="h-meta-item"><strong>Operaciones</strong>{total_ops}</div>
    <div class="h-meta-item"><strong>Async Tipo 2</strong>{n_async} confirmados</div>
  </div>
</header>
<nav>
  {nav_async}
  {nav_bpd}
  <a href="#is-modulos">🔌 IS por módulo</a>
</nav>
<div class="container">
{async_section}
{bpd_section}
{is_section}
</div>
<footer>
  <strong>NTT DATA EMEAL</strong> · IBM TWX Reverse Engineering Suite v{version} ·
  IS Parameters Report · {n_modules} módulos · {today} ·
  <strong>llopezdo@emeal.nttdata.com</strong>
</footer>
</body></html>"""
