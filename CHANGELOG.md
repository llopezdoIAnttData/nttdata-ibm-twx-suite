# Changelog

All notable changes to NTTDATA IBM TWX Suite are documented here.  
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
versioning follows [Semantic Versioning](https://semver.org/).

---

## [1.0.0] — 2025-07-01

### Added
- **9 analysis cycles** covering artefacts, entities, services, endpoints,
  entry points, flows, dependencies, scripts, and documentation
- **Interactive agentic CLI** (`run_analysis.py`) with animated sub-agent
  processing display and interactive file-path prompt
- **XML extractor** for key TWX internals: manifest, UCAs (4.*), BOs (12.*),
  BPDs (25.*), Coach Views (64.*)
- **Copilot skills** for each cycle (`twx-analyze` through `twx-docs`) and
  master orchestrator (`twx-suite`)
- **Profuturo v3 methodology** skill with 11 critical correction rules
- **NTT DATA branded terminal banner** (256-color ANSI, bright blue)
- **COPILOT_PROMPT.md** generator with full v3 methodology context
- GitHub Copilot CLI integration via `.copilot/skills/` and `.copilot/agents/`

### Fixed
- sequenceFlow step ordering (replaces X/Y coordinate ordering)
- Button extraction from `64.*.xml` coach views (replaces textual descriptions)
- `PostponeAction` correctly mapped to "Cerrar tarea en Appian"
- IG Revisión UDI classified as synchronous integration

---

## [Unreleased]

- Web UI for uploading TWX and viewing results in browser
- Parallel execution of analysis cycles
- Diff mode to compare two TWX versions

[1.0.0]: https://github.com/llopezdo/nttdata-ibm-twx-suite/releases/tag/v1.0.0
