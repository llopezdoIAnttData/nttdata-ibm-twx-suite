---
name: nttdata
description: >
  NTT DATA skills launcher and menu. Use this skill when the user types
  "nttdata", "/nttdata", "menu nttdata", "herramientas nttdata", or asks
  what NTT DATA tools are available. Shows a branded menu of all installed
  NTT DATA skills and lets the user pick one to execute immediately.
allowed-tools: shell
---

# 🔷 NTT DATA — Skills Launcher

Cuando este skill se activa, muestra el siguiente menú en pantalla y
espera a que el usuario elija una opción para ejecutarla.

---

## PASO 1 — Mostrar el menú

Imprime **exactamente** este bloque en la respuesta (sin modificarlo):

```
╔══════════════════════════════════════════════════════════════╗
║           🔷  NTT DATA  —  Skills Launcher                  ║
║          IBM TWX Reverse Engineering Suite v1.0.0           ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  ANÁLISIS TWX (archivo único)                                ║
║  ─────────────────────────────────────────────────────────  ║
║  [1]  analyze-Twx-Extract  — Pipeline completo + HTML       ║
║  [2]  twx-suite            — Suite completa (9 ciclos)      ║
║  [3]  twx-analyze          — Resumen de artefactos          ║
║  [4]  twx-entities         — Business Objects y modelos     ║
║  [5]  twx-services         — Servicios, pasos, lógica       ║
║  [6]  twx-flows            — Diagramas Mermaid de flujos    ║
║  [7]  twx-deps             — Grafo de dependencias          ║
║  [8]  twx-endpoints        — Endpoints REST/SOAP externos   ║
║  [9]  twx-scripts          — Scripts JavaScript embebidos   ║
║  [10] twx-entries          — Entry points / API pública     ║
║  [11] twx-docs             — Documentación Markdown         ║
║                                                              ║
║  ANÁLISIS MULTI-TWX (N ficheros)                             ║
║  ─────────────────────────────────────────────────────────  ║
║  [12] twx-multi-entities   — Modelo cruzado N ficheros HTML ║
║                                                              ║
║  MIGRACIÓN IBM BPM → APPIAN                                  ║
║  ─────────────────────────────────────────────────────────  ║
║  [13] profuturo-twx        — Metodología v3 Profuturo       ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝

  👉  Escribe el número o el nombre del skill a ejecutar.
      Escribe "todos" para ver una descripción de cada uno.
```

---

## PASO 2 — Responder a la elección del usuario

Cuando el usuario responda con un número o nombre, invoca el skill
correspondiente según esta tabla:

| Opción | Skill a invocar         |
|--------|------------------------|
| 1      | `analyze-Twx-Extract`  |
| 2      | `twx-suite`            |
| 3      | `twx-analyze`          |
| 4      | `twx-entities`         |
| 5      | `twx-services`         |
| 6      | `twx-flows`            |
| 7      | `twx-deps`             |
| 8      | `twx-endpoints`        |
| 9      | `twx-scripts`          |
| 10     | `twx-entries`          |
| 11     | `twx-docs`             |
| 12     | `twx-multi-entities`  |
| 13     | `profuturo-twx`        |

Si el usuario escribe `todos`, muestra esta descripción expandida:

| # | Skill | Cuándo usarlo |
|---|-------|---------------|
| 1 | **analyze-Twx-Extract** | Pipeline completo: extrae XMLs, ejecuta 9 ciclos y genera reporte HTML navegable. Es el punto de entrada recomendado. |
| 2 | **twx-suite** | Orquestador maestro. Decide qué ciclos ejecutar según la pregunta del usuario. |
| 3 | **twx-analyze** | Solo quieres saber cuántos artefactos hay y qué tipos. Respuesta rápida en JSON. |
| 4 | **twx-entities** | Necesitas el modelo de datos: Business Objects, campos, herencia. |
| 5 | **twx-services** | Quieres ver los servicios IS/HHS/GSS con sus pasos y lógica interna. |
| 6 | **twx-flows** | Quieres diagramas de flujo Mermaid de cada proceso o servicio. |
| 7 | **twx-deps** | Quieres el grafo de llamadas entre artefactos (quién llama a quién). |
| 8 | **twx-endpoints** | Buscas las URLs REST/SOAP/WSDL a sistemas externos. |
| 9 | **twx-scripts** | Quieres ver todo el código JavaScript/Groovy embebido. |
| 10 | **twx-entries** | Necesitas identificar los artefactos que nadie llama (API pública / UCAs). |
| 11 | **twx-docs** | Genera documentación Markdown completa del TWX. |
| 12 | **twx-multi-entities** | Analiza N ficheros .twx a la vez. Encuentra BOs compartidos, clusters estructurales y genera un HTML unificado con el patrón del modelo de datos y oportunidades de reutilización. |
| 13 | **profuturo-twx** | Migración IBM BPM → Appian con las 11 correcciones validadas del equipo Profuturo. |

---

## Notas
- Todos los skills trabajan con archivos `.twx` de IBM BPM / IBM BAW.
- Herramienta base: `python -m ibm_twx_tools` en
  `C:\Users\llopezdo\OneDrive - NTT DATA EMEAL\Documentos\NTTDATAIBMTWXSuite\NTTDATA-IBM-TWX-Suite\01_herramientas_python`
- Requiere Python 3.9+ con `ibm_twx_tools` instalado (`pip install -e .`).
