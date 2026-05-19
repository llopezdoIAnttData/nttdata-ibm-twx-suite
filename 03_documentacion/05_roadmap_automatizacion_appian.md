# NTT DATA · IBM TWX Suite — Roadmap de Automatización Completa
## IBM BPM → Appian: del TWX al import automático

> **Autor:** llopezdo@emeal.nttdata.com · **Suite:** v1.0 → v2.0 (objetivo)
> **Estado:** Fases 1–2 en producción · Fases 3–5 en construcción

---

## Visión: 1 comando, 1 resultado

```
python full_pipeline.py "Profuturo_Redencion_Bono_AP.twx"
                              ↓
                   appian-package.zip
              (listo para importar en Appian Designer)
```

| Hoy (Suite v1) | Objetivo (Suite v2) | Visión final (Suite v2+) | Reducción total |
|---|---|---|---|
| ~2h 45min | ~45 min | ~15 min | **−98% vs. manual** |

---

## El problema que resuelve la automatización completa

La Suite v1 automatiza la **extracción y el análisis**. El analista todavía debe:

1. Leer el reporte de Arquitectura de Conocimiento
2. Crear manualmente los objetos en Appian Designer (Record Types, Interfaces, Constants, etc.)
3. Configurar las integraciones y los process models
4. Verificar que todo esté correctamente referenciado

Este trabajo manual en Appian toma entre **4 y 8 horas adicionales** por proceso migrado.

**La Suite v2 elimina ese trabajo** generando directamente el paquete de importación de Appian.

---

## Pipeline completo: 5 fases

```
┌──────────────────────────────────────────────────────────────────────────┐
│  ENTRADA: archivo.twx            SALIDA: appian-package.zip              │
└──────────────────────────────────────────────────────────────────────────┘

FASE 1          FASE 2          FASE 3          FASE 4          FASE 5
────────────    ────────────    ────────────    ────────────    ────────────
Extracción      Análisis        Mapeo de        Generación      Import
automática  →   con Copilot →   objetos     →   XML Appian  →   Package
TWX                             IBM→Appian

run_analysis    skill           object_         appian_         .zip listo
.py             profuturo-twx   mapper.py       generator.py

✓ EXISTE        ✓ EXISTE        ⚡ CONSTRUIR    ⚡ CONSTRUIR    🔭 OBJETIVO

~10 min         ~2h 30min       ~5 min          ~10 min         Importar
```

### Estado de cada fase

| Fase | Nombre | Estado | Tiempo |
|---|---|---|---|
| 1 | Extracción automática TWX | ✅ Suite v1 — En producción | ~10 min |
| 2 | Análisis con Copilot CLI | ✅ Suite v1 — En producción | ~2h 30min |
| 3 | Motor de mapeo IBM BPM → Appian | ⚡ En construcción | ~5 min |
| 4 | Generador de XML Appian | ⚡ En construcción | ~10 min |
| 5 | Appian Import Package (.zip) | 🔭 Objetivo final | ~5 min import |

---

## Mapeo de objetos: IBM BPM → Appian

El núcleo de la automatización es el motor de mapeo. Esta tabla define cómo cada artefacto IBM BPM se convierte en un objeto Appian.

| Objeto IBM BPM | Prefijo XML | Cantidad | → Objeto Appian | Archivo generado | Complejidad |
|---|---|---|---|---|---|
| Business Object | `12.*.xml` | 54 | Record Type + Data Type | `.recordType.xml` · `.dataType.xml` | Media |
| BPD / Proceso | `25.*.xml` | 44 | Process Model | `.process.xml` | **Alta** |
| HHS (Human Service) | `1.*.xml` (type=3) | 23 | Interface (SAIL) | `.interface.xml` | **Alta** |
| GSS (General System) | `1.*.xml` (type=6) | 24 | Expression Rule / Process | `.rule.xml` · `.process.xml` | Media |
| IS (Integration Service) | `1.*.xml` (type=4) | 22 | Integration Object | `.integration.xml` | Media |
| Coach View (Botón/UI) | `64.*.xml` | 39 | Interface Component | `.interface.xml` (embedded) | Media |
| UCA (Undercover Agent) | `4.*.xml` | 15 | Process Event Handler | `.process.xml` (async) | Media |
| Variables de entorno | `62.*.xml` | 1 set | Constants | `.constant.xml` (×N vars) | **Baja** |
| Endpoints REST/SOAP | detectados en IS | N URLs | Connected System | `.connectedSystem.xml` | **Baja** |
| Scripts JavaScript | embedded | 455 KB | Expression Rule (via Copilot) | `.rule.xml` | **Alta + IA** |

### Reglas críticas de mapeo (de la Metodología v3)

Estas reglas se aplican **automáticamente** durante el mapeo:

| Regla | IBM BPM | → Appian |
|---|---|---|
| Orden de pasos | `sequenceFlow` (NUNCA X/Y) | Orden real en Process Model |
| Botones HHS | Siempre desde `64.*.xml` | Interface components correctos |
| `PostponeAction` | "Cerrar tarea en Appian" | Acción correcta en task node |
| IS Revisión UDI | SÍNCRONO (sin nodo UCA) | Integración directa sin evento |
| Env vars | `62.*.xml` (no manifest) | Constants con valores correctos |
| ID producción | `8628` en PROD, `8627` en otros | Constants por entorno |

---

## Los 6 módulos del generador

### 01 · `BusinessObjectMapper`
**Complejidad:** Media · **Output:** `.recordType.xml` + `.dataType.xml`

```python
# Input:  02_entities.json (de entity_extractor.py)
#         12.*.xml (twClass)
# Output: records/{nombre}.recordType.xml
#         types/{nombre}.dataType.xml

bo_mapper.convert(entities_json, output_dir)
# Mapea: campos → fields, tipos → Appian types, herencia → parent record
```

**Conversión de tipos:**
| IBM BPM | → Appian |
|---|---|
| `String` | `Text` |
| `Integer` | `Integer` |
| `Decimal` | `Decimal` |
| `Date` | `Date` |
| `Boolean` | `Boolean` |
| `{BusinessObject}` | `{RecordType}` (referencia) |

---

### 02 · `HHSInterfaceMapper` + Copilot
**Complejidad:** Alta · **Output:** `.interface.xml`

```python
# Input:  03_services.json (type=service_hhs)
#         64.*.xml (Coach Views → botones)
# ⚠️ CRÍTICO: botones SIEMPRE desde 64.*.xml
# Output: interfaces/{nombre}.interface.xml (SAIL)

hhs_mapper.convert(services_hhs, coach_views_xml, output_dir)
# Copilot CLI genera el SAIL inicial ciclo por ciclo
```

---

### 03 · `ISIntegrationMapper`
**Complejidad:** Media · **Output:** `.integration.xml` + `.connectedSystem.xml`

```python
# Input:  03_services.json (type=service_is)
#         07_endpoints.txt (URLs detectadas)
# Output: integrations/{nombre}.integration.xml
#         connectedSystems/{sistema}.connectedSystem.xml

is_mapper.convert(services_is, endpoints, output_dir)
```

---

### 04 · `EnvVarConstantMapper`
**Complejidad:** Baja · **Output:** `.constant.xml` (uno por variable)

```python
# Input:  xml_extracts/62.*.xml (environmentVariableSet)
# Output: constants/{nombre}.constant.xml
# ⚠️ ID_SUBETAPA: 8627 (Dev/Test) · 8628 (PROD)

env_mapper.convert(env_vars_xml, output_dir)
# 1:1 conversión tw.env.X → Appian Constant X
```

---

### 05 · `BPDProcessMapper`
**Complejidad:** Alta · **Output:** `.process.xml`

```python
# Input:  25.*.xml (bpd)
#         06_flows.txt (sequenceFlow ya resuelto)
# Output: processes/{nombre}.process.xml
# ⚠️ Orden: SIEMPRE sequenceFlow, nunca coordenadas X/Y

bpd_mapper.convert(bpd_xmls, flows_txt, output_dir)
# Mapea: tareas humanas → user tasks, servicios → service tasks
#        gateways → gateways, eventos → start/end events
```

---

### 06 · `JSExpressionMapper` + Copilot CLI
**Complejidad:** Alta · **Requiere IA** · **Output:** `.rule.xml`

```python
# Input:  08_scripts.txt (455 KB JavaScript)
# Proceso: Copilot CLI skill "appian-translator" traduce JS → Appian
# Output: expressionRules/{nombre}.rule.xml

js_mapper.translate_with_copilot(scripts_txt, output_dir)
```

**Patrones de traducción JS → Appian:**
| JavaScript IBM BPM | → Appian Expression Language |
|---|---|
| `tw.local.nombreVar` | `local!nombreVar` |
| `tw.env.CONSTANTE` | `cons!CONSTANTE` |
| `tw.process.campo` | `pv!campo` |
| `new tw.object.ClienteType()` | `a!localVariable(type: ClienteType)` |
| `if (condicion) { ... }` | `if(condicion, ..., ...)` |
| `for (var i in lista)` | `a!forEach(items: lista, ...)` |

---

## Estructura del paquete `appian-package.zip`

```
appian-package/
├── application.xml                  ← Manifiesto (nombre, versión, dependencias)
│
├── content/
│   ├── records/                     ← 54 Record Types (desde Business Objects)
│   │   ├── Cliente.recordType.xml
│   │   ├── Solicitud.recordType.xml
│   │   └── ... (54 archivos)
│   │
│   ├── dataTypes/                   ← 54 Data Types (estructura de los BOs)
│   │   └── ... (54 archivos)
│   │
│   ├── processes/                   ← 44 BPDs + 24 GSS = 68 Process Models
│   │   ├── RedencionBono.process.xml
│   │   ├── ValidacionUDI.process.xml
│   │   └── ... (68 archivos)
│   │
│   ├── interfaces/                  ← 23 Interfaces SAIL (desde HHS + Coach Views)
│   │   ├── PantallaSolicitud.interface.xml
│   │   └── ... (23 archivos)
│   │
│   ├── constants/                   ← N Constants (desde tw.env.*)
│   │   ├── ID_SUBETAPA_DEV.constant.xml    ← valor: 8627
│   │   ├── ID_SUBETAPA_PROD.constant.xml   ← valor: 8628
│   │   └── ... (N archivos)
│   │
│   ├── integrations/                ← 22 Integration Objects (desde IS)
│   │   ├── IntegracionUDI.integration.xml
│   │   └── ... (22 archivos)
│   │
│   ├── connectedSystems/            ← Connected Systems (desde endpoints)
│   │   └── SistemaUDI.connectedSystem.xml
│   │
│   └── expressionRules/             ← Expression Rules (JS → Appian, via Copilot)
│       ├── calcularMonto.rule.xml
│       └── ... (scripts traducidos)
│
└── README.md                        ← Instrucciones de importación y notas
```

### Pasos para importar en Appian Designer

```
1. python full_pipeline.py "archivo.twx"
             ↓
2. Abrir Appian Designer
             ↓
3. Aplicaciones → Administrar → Importar
             ↓
4. Seleccionar output/appian-package.zip
             ↓
5. ✅ Objetos disponibles para configurar y publicar
```

---

## Roadmap de desarrollo

### ✅ Sprint 0 — COMPLETADO: Suite v1

- ✓ `twx_parser.py` v2 — parser ZIP/XML con prefijos
- ✓ `run_analysis.py` — 9 comandos CLI en cadena
- ✓ `COPILOT_PROMPT.md` — prompt maestro 57 KB
- ✓ `skill profuturo-twx` — metodología v3 en Copilot
- ✓ 11 correcciones v3 validadas en producción
- ✓ 232 artefactos procesados (Profuturo v1.17.51)

---

### ⚡ Sprint 1 — EN CONSTRUCCIÓN: Suite v2 Alpha

**Objetivo:** Motor de mapeo + generadores de baja complejidad

- ○ `object_mapper.py` (clase base)
- ○ `EnvVarConstantMapper` — `62.*.xml` → `.constant.xml`
- ○ `BusinessObjectMapper` — `12.*.xml` → `.dataType.xml`
- ○ `ConnectedSystemMapper` — endpoints → `.connectedSystem.xml`
- ○ `appian_package_builder.py` — construye el ZIP
- ○ Validación del formato XML de Appian

---

### ⚡ Sprint 2 — PLANIFICADO: Suite v2 Beta

**Objetivo:** Mappers de complejidad media + paquete parcial importable

- ○ `BusinessObjectMapper` → `.recordType.xml` (con relaciones)
- ○ `ISIntegrationMapper` → `.integration.xml`
- ○ `GSS → Expression Rules` (lógica simple sin JS complejo)
- ○ `UCAProcessMapper` → `.process.xml` (async handlers)
- ○ `appian_generator.py` — CLI unificado
- ○ Test de importación con paquete parcial en Appian Dev

---

### 🔭 Sprint 3 — VISIÓN: Suite v2 Completa

**Objetivo:** Pipeline end-to-end completo con traducción JS → Appian

- ○ `BPDProcessMapper` — flujos completos con `sequenceFlow`
- ○ `HHSInterfaceMapper` — Interfaces SAIL con Copilot
- ○ `JSExpressionMapper` + skill `appian-translator`
- ○ `full_pipeline.py` — un único comando de inicio a fin
- ○ Importación completa validada en Appian Designer
- ○ Suite v2 documentada y lista para nuevos proyectos

---

## Impacto estimado de la automatización completa

| Métrica | Suite v1 (hoy) | Suite v2 (objetivo) | Mejora |
|---|---|---|---|
| Tiempo total por proceso | ~2h 45min | ~15–45 min | **−83% adicional** |
| Tiempo vs. proceso manual | −83% | **−98%** | Máximo posible |
| Intervención humana | Análisis Copilot | Solo revisión final | Mínima |
| Objetos Appian creados a mano | Todos | Cero (generados) | **100% automático** |
| Escalabilidad a otros TWX | ✓ Análisis | ✓ Análisis + Generación | Sin límite |
| Onboarding nuevo proyecto | ~3h análisis | ~1 comando | Inmediato |

### El comando final (visión)

```bash
# Suite v2 — Un comando, pipeline completo
python full_pipeline.py "MiApp.twx"

  ✓ Fase 1 — Extracción TWX          (~10 min)
  ✓ Fase 2 — Análisis Copilot        (~2h 30min)  ← puede omitirse si solo se necesita import
  ⚡ Fase 3 — Mapeo IBM BPM → Appian  (~5 min)
  ⚡ Fase 4 — Generación XML Appian   (~10 min)
  🔭 Fase 5 — Build appian-package.zip

  ✓ Listo: output/appian-package.zip
    ├── 54 Record Types
    ├── 68 Process Models (44 BPDs + 24 GSS)
    ├── 23 Interfaces SAIL
    ├── N  Constants (tw.env.*)
    ├── 22 Integration Objects
    └── N  Expression Rules (JS → Appian)

  Importar: Appian Designer → Aplicaciones → Importar → appian-package.zip
```

---

## Archivos del proyecto por fase

| Fase | Archivo | Descripción |
|---|---|---|
| 1 (existe) | `run_analysis.py` | Pipeline extracción: 9 comandos CLI |
| 1 (existe) | `ibm_twx_tools/twx_parser.py` | Parser ZIP/XML TWX |
| 1 (existe) | `ibm_twx_tools/service_extractor.py` | Servicios IS/GSS/HHS |
| 2 (existe) | `~/.copilot/skills/profuturo-twx/` | Skill Copilot v3 |
| 3 (nuevo) | `appian_tools/object_mapper.py` | Motor de mapeo base |
| 3 (nuevo) | `appian_tools/bo_mapper.py` | Business Objects → Record Types |
| 3 (nuevo) | `appian_tools/env_mapper.py` | Env vars → Constants |
| 3 (nuevo) | `appian_tools/is_mapper.py` | IS → Integration Objects |
| 4 (nuevo) | `appian_tools/appian_generator.py` | Generador XML Appian |
| 4 (nuevo) | `appian_tools/bpd_mapper.py` | BPDs → Process Models |
| 4 (nuevo) | `appian_tools/hhs_mapper.py` | HHS → Interfaces SAIL |
| 4 (nuevo) | `appian_tools/js_mapper.py` | JS → Expression Rules (+ Copilot) |
| 5 (nuevo) | `appian_tools/package_builder.py` | Construye el ZIP final |
| 5 (nuevo) | `full_pipeline.py` | Comando único end-to-end |

---

*NTT DATA · IBM TWX Reverse Engineering Suite · v1.0 → v2.0*
*llopezdo@emeal.nttdata.com · IBM Integration Services · Legacy Migration · EMEAL*
*© 2026 NTT DATA*
