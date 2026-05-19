# 🔷 NTTDATA IBM TWX — Reverse Engineering Suite

> **Industrialized agentic toolchain for extracting and documenting IBM BPM TWX
> process artefacts, integrated with GitHub Copilot CLI.**

[![Python 3.9+](https://img.shields.io/badge/Python-3.9%2B-blue?logo=python)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![GitHub Copilot](https://img.shields.io/badge/GitHub%20Copilot-Skills-blueviolet?logo=github)](https://copilot.github.com/)
[![NTT DATA](https://img.shields.io/badge/NTT%20DATA-EMEAL-00a3e0)](https://es.nttdata.com/)

---

## Overview

This suite reverse-engineers IBM BPM TWX export files (`.twx`) through
**9 automated analysis cycles**, each backed by a dedicated GitHub Copilot
skill. The result is a machine-readable extraction + a structured Copilot
prompt ready for migration analysis (IBM BPM → Appian / other platforms).

```
📦 .twx file  →  9 cycles  →  COPILOT_PROMPT.md  →  Copilot CLI
```

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🤖 **Agentic CLI** | Interactive prompt — just run `python run_analysis.py` |
| 🔄 **9 Analysis Cycles** | Artefacts, Entities, Services, Endpoints, Entry Points, Flows, Dependencies, Scripts, Docs |
| 📦 **XML Extractor** | Auto-extracts UCAs, BOs, BPDs, Coach Views, and manifest from TWX zip |
| 🧠 **Copilot Skills** | 10 skills + 1 master agent wired to GitHub Copilot CLI |
| 📄 **v3 Methodology** | 11 critical corrections from real team feedback (Profuturo case) |
| 🎨 **NTT DATA Banner** | 256-color ANSI terminal branding |

---

## 🗂️ Repository Structure

```
NTTDATA-IBM-TWX-Suite/
├── run_analysis.py               ← Interactive agentic entry point
├── 01_herramientas_python/
│   └── ibm_twx_tools/
│       ├── __main__.py           ← Module entry point
│       ├── cli.py                ← 9 commands (analyze, entities, …)
│       ├── banner.py             ← NTT DATA ANSI banner
│       └── analyzers/           ← Per-cycle analysis logic
├── 02_skills_copilot/
│   └── skills_setup.md          ← How to install Copilot skills
├── 03_documentacion/
│   ├── 06_que_hicimos.html       ← Project briefing
│   └── 07_skills_guia.html       ← Skills & agent visual guide
├── index.html                   ← Main project dashboard
├── .copilot/
│   ├── skills/
│   │   ├── twx-suite/           ← Master orchestrator skill
│   │   ├── twx-analyze/         ← Cycle 1
│   │   ├── twx-entities/        ← Cycle 2
│   │   ├── twx-services/        ← Cycle 3
│   │   ├── twx-endpoints/       ← Cycle 4 (Endpoints)
│   │   ├── twx-entries/         ← Cycle 5 (Entry Points / UCAs)
│   │   ├── twx-flows/           ← Cycle 6
│   │   ├── twx-deps/            ← Cycle 7
│   │   ├── twx-scripts/         ← Cycle 8
│   │   ├── twx-docs/            ← Cycle 9
│   │   └── profuturo-twx/       ← v3 Profuturo methodology
│   └── agents/
│       └── twx-engineer.md      ← Master agent (6 phases)
├── README.md
├── CONTRIBUTING.md
├── CHANGELOG.md
└── LICENSE
```

---

## 🚀 Quick Start

### 1. Install Python tools

```bash
cd 01_herramientas_python
pip install -e .
```

### 2. Verify installation

```bash
python -m ibm_twx_tools --help
```

### 3. Run the agentic analysis

```bash
cd NTTDATA-IBM-TWX-Suite
python run_analysis.py
```

The CLI will show the NTT DATA banner and prompt:

```
  ▸ Agente de Extracción TWX listo
  Este proceso ejecutará 9 ciclos de análisis + extracción XML

  📁 Ruta del archivo .TWX: _
```

Paste the relative or absolute path to your `.twx` file and press Enter.
The suite will run all 9 cycles with animated sub-agent labels:

```
  ──────────────────────────────────────────────────────
    FASE 1  Extracción automática — 9 Ciclos
    sub-agente: twx-suite / ciclos 1-9
  ──────────────────────────────────────────────────────

    ✓  Ciclo 1 · Resumen de artefactos    [twx-analyze]  → 01_analyze.json  (12.4 KB)
    ✓  Ciclo 2 · Business Objects         [twx-entities] → 02_entities.json (8.1 KB)
    ...
```

### 4. Use the generated prompt with Copilot

```bash
# Open COPILOT_PROMPT.md in your editor, then in Copilot CLI:
gh copilot suggest "$(cat output/MyProcess/COPILOT_PROMPT.md)"
```

---

## 📋 Analysis Cycles

| Cycle | Command | Output | Copilot Skill |
|-------|---------|--------|---------------|
| 1 | `analyze` | `01_analyze.json` | `twx-analyze` |
| 2 | `entities` | `02_entities.json` | `twx-entities` |
| 3 | `services` | `03_services.json` | `twx-services` |
| 4 | `endpoints` | `04_endpoints.json` | `twx-endpoints` |
| 5 | `entries` | `05_entries.json` | `twx-entries` |
| 6 | `flows` | `06_flows.txt` | `twx-flows` |
| 7 | `deps` | `07_deps.txt` | `twx-deps` |
| 8 | `scripts` | `08_scripts.txt` | `twx-scripts` |
| 9 | `docs` | `09_docs.md` | `twx-docs` |

---

## 🧠 Copilot Skills

Install skills by copying the `.copilot/` directory to your user profile:

```powershell
# Windows
Copy-Item -Recurse .copilot\skills\* "$env:USERPROFILE\.copilot\skills\"
Copy-Item -Recurse .copilot\agents\* "$env:USERPROFILE\.copilot\agents\"
```

```bash
# Linux / macOS
cp -r .copilot/skills/* ~/.copilot/skills/
cp -r .copilot/agents/* ~/.copilot/agents/
```

Then use in Copilot CLI:

```bash
# Run a specific cycle skill
gh copilot chat --skill twx-analyze

# Run the full suite skill
gh copilot chat --skill twx-suite

# Use the Profuturo v3 methodology
gh copilot chat --skill profuturo-twx
```

---

## ⚙️ Individual Commands

You can also run cycles individually without the agentic pipeline:

```bash
cd 01_herramientas_python
python -m ibm_twx_tools analyze   "C:\path\to\Process.twx"
python -m ibm_twx_tools entities  "C:\path\to\Process.twx"
python -m ibm_twx_tools services  "C:\path\to\Process.twx"
python -m ibm_twx_tools endpoints "C:\path\to\Process.twx"
python -m ibm_twx_tools entries   "C:\path\to\Process.twx"
python -m ibm_twx_tools flows     "C:\path\to\Process.twx"
python -m ibm_twx_tools deps      "C:\path\to\Process.twx"
python -m ibm_twx_tools scripts   "C:\path\to\Process.twx"
python -m ibm_twx_tools docs      "C:\path\to\Process.twx"
```

---

## 📐 TWX Artefact Prefix Taxonomy

| Prefix | Artefact Type |
|--------|--------------|
| `1.*` | Services (processType 3=HHS, 4=IS, 6=GSS) |
| `4.*` | UCAs (Undercover Agents) |
| `12.*` | Business Objects |
| `25.*` | BPDs (Business Process Definitions) |
| `62.*` | Environment variables |
| `64.*` | Coach Views (buttons / UI components) |

---

## 📝 v3 Methodology — Critical Rules

The `profuturo-twx` skill enforces 11 corrections validated with a real
migration team:

1. Step ordering by `sequenceFlow`, not by X/Y coordinates
2. Buttons extracted from `64.*.xml` (not from textual descriptions)
3. `PostponeAction` mapped to "Cerrar tarea"
4. IG Revisión UDI classified as synchronous
5. Environment variables from `62.*.xml` (not from MANIFEST)
6. Dev environment ID ≠ Prod environment ID
7–11. XML structural rules (BO in `12.*`, UCA folio correlation, etc.)

---

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for setup, coding standards, and PR
process.

---

## 📜 License

[MIT](LICENSE) © 2025 NTT DATA EMEAL

---

## 🔗 Related

- [IBM BPM documentation](https://www.ibm.com/docs/en/bpm)
- [GitHub Copilot CLI](https://docs.github.com/en/copilot/using-github-copilot/using-github-copilot-in-the-command-line)
- [Appian BPM Platform](https://appian.com/)
