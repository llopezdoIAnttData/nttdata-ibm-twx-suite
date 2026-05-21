# 🔷 NTTDATA IBM TWX — Reverse Engineering Suite

> **Toolchain agentic industrializada para extraer, documentar y comparar artefactos de procesos IBM BPM / IBM BAW, integrada con GitHub Copilot CLI.**

[![Python 3.9+](https://img.shields.io/badge/Python-3.9%2B-blue?logo=python)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![GitHub Copilot](https://img.shields.io/badge/GitHub%20Copilot-Skills-blueviolet?logo=github)](https://copilot.github.com/)
[![NTT DATA](https://img.shields.io/badge/NTT%20DATA-EMEAL-00a3e0)](https://es.nttdata.com/)
[![Skills](https://img.shields.io/badge/Skills-15-success)](https://github.com/llopezdoIAnttData/nttdata-ibm-twx-suite)

---

## ¿Qué hace esta suite?

La suite convierte un archivo `.twx` de IBM BPM (o un conjunto de ellos) en conocimiento estructurado:

```
📦 .twx  →  9 ciclos de extracción  →  JSON / Markdown / HTML
                                     →  Análisis IA de modelo de datos
                                     →  Reporte HTML navegable
                                     →  Prompt listo para Copilot CLI
```

**Caso de uso principal:** proyectos de migración IBM BPM / IBM BAW → Appian (u otra plataforma BPM). La suite automatiza la fase de *reverse engineering* que normalmente requiere semanas de lectura manual de XML.

**Capacidades clave:**
- Extrae todos los artefactos de un `.twx`: Business Objects, servicios IS/GSS/HHS, BPDs, Coach Views, UCAs, scripts, endpoints externos y variables de entorno.
- Genera diagramas de flujo Mermaid ordenados por `sequenceFlow` (no por coordenadas visuales).
- Analiza **N ficheros TWX en paralelo** y detecta Business Objects compartidos, clusters semánticos y candidatos a toolkit reutilizable.
- Integra metodología v3 validada con equipo real Profuturo (11 correcciones críticas documentadas).
- Se invoca directamente desde **GitHub Copilot CLI** o el **chat de GitHub Copilot** con skills de un solo comando.

---

## ✨ Novedades — v1.1.0

| Nuevo skill | Qué aporta |
|-------------|------------|
| 🔷 `nttdata` | Menú launcher unificado — punto de entrada para todos los skills |
| 🌐 `twx-multi-entities` | Análisis cruzado de N ficheros TWX con IA: BOs compartidos, clusters semánticos, HTML report |
| 🚀 `analyze-Twx-Extract` | Pipeline completo end-to-end: extrae XMLs + 9 ciclos + genera HTML navegable |
| 🎨 `dashboard-corporate-design` | Genera dashboards HTML con marca NTT DATA desde cualquier dato estructurado |

---

## ⌨️ Skills disponibles — Referencia rápida

Escribe el comando en el chat de GitHub Copilot o en Copilot CLI:

| # | Comando | Qué hace |
|---|---------|----------|
| 0 | `/nttdata` | **Menú launcher.** Muestra todos los skills y permite invocarlos por número. Punto de entrada recomendado. |
| 1 | `/analyze-Twx-Extract` | **Pipeline completo.** Pide la ruta del `.twx`, extrae XMLs, ejecuta 9 ciclos y genera un reporte HTML navegable. |
| 2 | `/twx-suite` | **Suite orquestadora.** Análisis guiado con los 9 ciclos. Ideal para sesiones de migración IBM BPM → Appian. |
| 3 | `/twx-analyze` | Resumen rápido de artefactos (conteo por tipo, versión, BPD principal). Primer vistazo a un TWX desconocido. |
| 4 | `/twx-entities` | Modelo de datos completo: Business Objects, campos, tipos y herencia. |
| 5 | `/twx-services` | Servicios IS/GSS/HHS con pasos, inputs/outputs, lógica y clasificación SYNC/ASYNC. |
| 6 | `/twx-flows` | Diagramas Mermaid de procesos y servicios en orden real (`sequenceFlow`). |
| 7 | `/twx-deps` | Grafo de dependencias entre artefactos (quién llama a quién). Análisis de impacto. |
| 8 | `/twx-endpoints` | URLs REST, HTTP y SOAP externas. Mapa de integraciones con sistemas externos. |
| 9 | `/twx-scripts` | Todo el JavaScript / Groovy embebido en servicios y BPDs con contexto de artefacto. |
| 10 | `/twx-entries` | Entry points: artefactos que ningún otro invoca (API pública / UCAs raíz). |
| 11 | `/twx-docs` | Documentación Markdown completa: BOs, servicios, flujos, scripts, endpoints y dependencias. |
| 12 | `/twx-multi-entities` | **Análisis cruzado N ficheros.** Detecta BOs compartidos, clusters semánticos y genera HTML unificado con IA. |
| 13 | `/profuturo-twx` | Metodología v3 Profuturo. Migración IBM BPM → Appian con 11 correcciones validadas. |

---

## 🗂️ Estructura del repositorio

```
NTTDATA-IBM-TWX-Suite/
├── run_analysis.py               ← Entry point agentic interactivo
├── 01_herramientas_python/
│   └── ibm_twx_tools/
│       ├── __main__.py           ← Módulo Python CLI
│       ├── cli.py                ← 9 comandos (analyze, entities, …)
│       ├── banner.py             ← Banner ANSI NTT DATA 256 colores
│       └── analyzers/           ← Lógica de cada ciclo de análisis
├── 02_skills_copilot/
│   └── skills_setup.md          ← Instrucciones de instalación
├── 03_documentacion/
│   ├── 06_que_hicimos.html       ← Briefing del proyecto
│   └── 07_skills_guia.html       ← Guía visual de skills y agente
├── index.html                   ← Dashboard principal del proyecto
├── .copilot/
│   ├── skills/
│   │   ├── nttdata/             ← 🆕 Launcher menu (punto de entrada)
│   │   ├── analyze-Twx-Extract/ ← 🆕 Pipeline completo end-to-end
│   │   ├── twx-suite/           ← Master orchestrator (9 ciclos)
│   │   ├── twx-analyze/         ← Ciclo 1 · Resumen de artefactos
│   │   ├── twx-entities/        ← Ciclo 2 · Business Objects
│   │   ├── twx-services/        ← Ciclo 3 · Servicios y lógica
│   │   ├── twx-flows/           ← Ciclo 4 · Diagramas Mermaid
│   │   ├── twx-endpoints/       ← Ciclo 5 · URLs externas
│   │   ├── twx-entries/         ← Ciclo 6 · Entry points / UCAs
│   │   ├── twx-deps/            ← Ciclo 7 · Grafo de dependencias
│   │   ├── twx-scripts/         ← Ciclo 8 · Scripts JS embebidos
│   │   ├── twx-docs/            ← Ciclo 9 · Documentación Markdown
│   │   ├── twx-multi-entities/  ← 🆕 Análisis cruzado N ficheros TWX
│   │   ├── profuturo-twx/       ← Metodología v3 Profuturo
│   │   └── dashboard-corporate-design/ ← 🆕 Dashboards HTML NTT DATA
│   └── agents/
│       └── twx-engineer.md      ← Agente maestro (6 fases)
├── README.md
├── CONTRIBUTING.md
├── CHANGELOG.md
└── LICENSE
```

---

## 🚀 Inicio rápido

### 1. Instalar las herramientas Python

```bash
cd 01_herramientas_python
pip install -e .
```

### 2. Verificar la instalación

```bash
python -m ibm_twx_tools --help
```

### 3. Instalar los skills en Copilot CLI

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

### 4. Invocar desde Copilot

Abre un chat de GitHub Copilot (VS Code, CLI, o web) y escribe:

```
/nttdata
```

El menú launcher mostrará todos los skills disponibles. Elige el número o nombre del skill a ejecutar.

---

## 📋 Los 9 ciclos de análisis

| Ciclo | Comando | Salida | Skill |
|-------|---------|--------|-------|
| 1 | `analyze` | `01_analyze.json` | `twx-analyze` |
| 2 | `entities` | `02_entities.json` | `twx-entities` |
| 3 | `services` | `03_services.json` | `twx-services` |
| 4 | `endpoints` | `04_endpoints.json` | `twx-endpoints` |
| 5 | `entries` | `05_entries.json` | `twx-entries` |
| 6 | `flows` | `06_flows.txt` | `twx-flows` |
| 7 | `deps` | `07_deps.txt` | `twx-deps` |
| 8 | `scripts` | `08_scripts.txt` | `twx-scripts` |
| 9 | `docs` | `09_docs.md` | `twx-docs` |

También se pueden ejecutar individualmente:

```bash
cd 01_herramientas_python
python -m ibm_twx_tools analyze   "C:\ruta\al\Proceso.twx"
python -m ibm_twx_tools entities  "C:\ruta\al\Proceso.twx"
python -m ibm_twx_tools services  "C:\ruta\al\Proceso.twx"
# ... (idem para el resto de comandos)
```

---

## 🌐 Análisis multi-TWX (`twx-multi-entities`)

Para comparar el modelo de datos entre varios proyectos IBM BPM:

```
/twx-multi-entities
```

El skill pedirá la carpeta que contiene los `.twx`, extraerá los BOs de cada uno con el CLI Python, y realizará un análisis semántico con IA que produce:

- **BOs compartidos exactos** — mismo nombre en 2+ proyectos
- **Clusters semánticos** — agrupaciones por dominio (pagos, afiliación, retiros…)
- **Score de reutilización** — métrica 0-100 que indica qué porcentaje del modelo de datos es candidato a biblioteca compartida
- **Candidatos a toolkit** — BOs que deberían vivir en un proyecto toolkit común
- **Inventario de reutilización** — tabla por frecuencia, por par de proyectos y por porcentaje de cobertura de cada app
- **Reporte HTML standalone** — archivo `.html` que se puede compartir sin dependencias externas

---

## 📐 Taxonomía de prefijos TWX

| Prefijo | Tipo de artefacto |
|---------|-------------------|
| `1.*` | Servicios (processType 3=HHS, 4=IS, 6=GSS) |
| `4.*` | UCAs (Undercover Agents) |
| `12.*` | Business Objects |
| `25.*` | BPDs (Business Process Definitions) |
| `62.*` | Variables de entorno |
| `64.*` | Coach Views (pantallas HHS + botones reales) |

---

## 📝 Metodología v3 — Reglas críticas (Profuturo)

El skill `profuturo-twx` aplica 11 correcciones validadas con el equipo real:

1. Ordenar pasos por `sequenceFlow`, nunca por coordenadas X/Y ni por orden XML
2. Botones extraídos de `64.*.xml` (`<boundaryEvent>` / `<postponeAction>`), NO de la descripción textual del servicio
3. `PostponeAction` → "Cerrar tarea en Appian" (no "Posponer")
4. IS "IG Revisión UDI" clasificado como SÍNCRONO (confirmado en v3)
5. Variables de entorno en `62.*.xml`, no en MANIFEST.MF
6. ID de entorno DEV ≠ ID de entorno PROD
7. BOs siempre en `12.*.xml`, nunca en otros prefijos
8. Correlación UCA-folio por nombre de servicio, no por GUID
9. Coach Views compuestas: revisar `<coachView>` anidados en `64.*.xml`
10. Servicios con `isForCompensation=true` → no son pasos del flujo principal
11. Clasificación SYNC/ASYNC por `processType` + presencia de `<messageFlow>`

---

## 🤝 Contributing

Ver [CONTRIBUTING.md](CONTRIBUTING.md) para setup, estándares de código y proceso de PR.

---

## 📜 Licencia

[MIT](LICENSE) © 2025 NTT DATA EMEAL

---

## 🔗 Referencias

- [IBM BPM documentation](https://www.ibm.com/docs/en/bpm)
- [GitHub Copilot CLI](https://docs.github.com/en/copilot/using-github-copilot/using-github-copilot-in-the-command-line)
- [Appian BPM Platform](https://appian.com/)
