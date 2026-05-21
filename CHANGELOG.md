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

## [1.1.0] — 2025-07-14

### Added
- **`nttdata` skill** — Menú launcher unificado. Muestra todos los skills disponibles y permite invocarlos por número o nombre. Punto de entrada recomendado para nuevos usuarios.
- **`twx-multi-entities` skill** — Análisis cruzado agentic de N ficheros `.twx`. Detecta Business Objects compartidos, clusters semánticos y genera reporte HTML standalone con análisis IA y score de reutilización.
- **`analyze-Twx-Extract` skill** — Pipeline end-to-end: extrae XMLs del TWX, ejecuta 9 ciclos de análisis y genera un reporte HTML navegable en un solo comando.
- **`dashboard-corporate-design` skill** — Genera dashboards HTML standalone con marca NTT DATA a partir de datos estructurados.
- **`SECURITY.md`** — Política de seguridad y proceso de reporte de vulnerabilidades.
- **`CODE_OF_CONDUCT.md`** — Código de conducta Contributor Covenant v2.1.
- **`SUPPORT.md`** — Canales de soporte y tiempos de respuesta.
- **`.github/CODEOWNERS`** — Asignación automática de reviewers por área del repo.
- **`.github/workflows/ci.yml`** — CI en GitHub Actions: lint Python (flake8) + validación de estructura de skills.
- **`.github/ISSUE_TEMPLATE/config.yml`** — Menú de selección de template con links a Discussions y Security Advisories.
- **`requirements.txt`** — Dependencias Python explícitas.
- `README.md` reescrito en español con tabla de shortcuts de skills, estructura actualizada y sección de análisis multi-TWX.
- `index.html` actualizado con tabla de referencia rápida de todos los skills y 4 nuevas cards.

### Fixed
- URL de repositorio incorrecta en `CONTRIBUTING.md` (`llopezdo` → `llopezdoIAnttData`)
- URL de release en `CHANGELOG.md` (`llopezdo` → `llopezdoIAnttData`)

## [Unreleased]

- Web UI para subir TWX y ver resultados en el navegador
- Ejecución paralela de ciclos de análisis
- Modo diff para comparar dos versiones de un TWX
- Soporte para IBM BAW 22.x (namespace `baw/20.0`)

[1.1.0]: https://github.com/llopezdoIAnttData/nttdata-ibm-twx-suite/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/llopezdoIAnttData/nttdata-ibm-twx-suite/releases/tag/v1.0.0
