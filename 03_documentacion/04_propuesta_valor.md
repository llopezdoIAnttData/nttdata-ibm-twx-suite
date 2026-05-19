# NTT DATA · IBM TWX Reverse Engineering Suite
## ¿Por qué usar esta suite? · Propuesta de valor

> **Autor:** llopezdo@emeal.nttdata.com · **Versión:** 1.0.0 · **Metodología:** v3

---

## De ~2 días de análisis a menos de 3 horas

| | Proceso manual | Con la suite |
|---|---|---|
| ⏱ Extracción de artefactos | ~4h | **~10 min** (`run_analysis.py`) |
| 🤖 Análisis con Copilot | — | **~2h 30min** (8 ciclos guiados) |
| 🔍 Revisión final | ~4h | **~15 min** |
| **Total** | **~16h (2 días)** | **~2h 45min** |
| **Reducción** | — | **−83%** del tiempo |

---

## El problema: ¿por qué el análisis manual de TWX es inviable?

Los archivos `.twx` de IBM BPM son ZIPs con cientos de XMLs anidados sin documentación de estructura. Hacer reverse engineering a mano requiere conocimiento profundo del formato interno, acceso a IBM Designer y días de trabajo.

### 🔍 Estructura opaca
Los artefactos están en `objects/{prefijo}.{guid}.xml`. Sin conocer la taxonomía de prefijos numéricos (`1.*` a `64.*`) es imposible saber qué archivo contiene qué tipo de artefacto.

### ⏳ Volumen masivo
Un TWX típico de producción contiene **200+ archivos XML**. Cada servicio puede tener decenas de pasos. Leer y cruzar todo de forma manual genera errores y demora días.

### 🐛 Errores críticos frecuentes
Sin las 11 correcciones de v3: orden de pasos incorrecto (coords X/Y en lugar de `sequenceFlow`), botones tomados del lugar equivocado, interpretación errónea de `PostponeAction`, IDs de entorno incorrectos en producción.

---

## Antes vs. Después

### ❌ Sin la suite — Proceso manual (~16 horas)

| Paso | Problema |
|---|---|
| Abrir IBM Designer | Navegar manualmente 232 artefactos. Sin filtros de tipo. Sin exportación masiva. |
| Identificar el MANIFEST | IBM BPM no tiene MANIFEST útil. El nombre de la app solo está en los BPDs. Confusión garantizada. |
| Documentar cada servicio | 74 servicios × ~15 pasos = miles de celdas en Excel. Horas de trabajo repetitivo. |
| Orden de pasos | El XML lista nodos por posición X/Y, no por flujo real. El orden documentado es erróneo sin leer `sequenceFlow`. |
| Variables de entorno | Los valores `tw.env.*` están en `62.*.xml`, no donde se espera. Fácil pasarlos por alto. |
| Generar el reporte | Escribir las 10 secciones de la Arquitectura de Conocimiento desde cero, cruzando múltiples fuentes. |

- **Tiempo:** ~16 horas
- **Probabilidad de error:** Alta
- **Reproducibilidad:** Nula — cada analista documenta diferente

---

### ✅ Con la suite — Automatizado (~2h 45min)

| Paso | Ventaja |
|---|---|
| 1 comando de extracción | `python run_analysis.py "archivo.twx"` — ejecuta 9 comandos CLI en cadena. 232 artefactos clasificados en ~10 min. |
| Taxonomía automática | El parser clasifica por prefijo numérico: 24 GSS · 23 HHS · 22 IS · 15 UCAs · 54 BOs · 44 BPDs · 39 Coach Views. |
| JSON estructurado | 8 archivos de output + 224 XMLs organizados por tipo. `COPILOT_PROMPT.md` (57 KB) pre-carga todo el contexto. |
| Orden real garantizado | El `flow_mapper` lee `<sequenceFlow>` explícitamente. Nunca usa coordenadas X/Y. 11 correcciones v3 validadas. |
| Variables de entorno capturadas | El parser detecta `62.*.xml` como `environmentVariableSet`. Todos los `tw.env.*` disponibles en el Ciclo 2. |
| 8 ciclos guiados | El skill `profuturo-twx` guía ciclo a ciclo. Las 10 secciones del reporte se generan con instrucciones precisas. |

- **Tiempo:** ~2h 45min
- **Probabilidad de error:** Mínima
- **Reproducibilidad:** Total — mismo resultado en cada ejecución

---

## Métricas reales (Profuturo Redención de Bono v1.17.51)

| Métrica | Valor |
|---|---|
| Artefactos totales extraídos | **232** |
| Comandos CLI ejecutados en cadena | **9 / 9 exitosos** |
| Servicios clasificados | **74** (24 GSS · 23 HHS · 22 IS) |
| Business Objects | **54** |
| UCAs (Undercover Agents) | **15** |
| BPDs (Procesos) | **44** |
| Coach Views (Botones/Pantallas) | **39** |
| XMLs organizados por prefijo | **224** |
| Tamaño del prompt maestro | **57 KB** |
| Scripts JavaScript extraídos | **455 KB** |
| Documentación Markdown generada | **378 KB** |
| Reducción de tiempo vs. manual | **−83%** |
| Correcciones v3 aplicadas | **11** |

---

## Pipeline de 3 fases

```
┌─────────────────────────────────────────────────────────┐
│     IBM BPM .twx  →  Arquitectura de Conocimiento       │
└─────────────────────────────────────────────────────────┘

  FASE 1                 FASE 2                 FASE 3
  ──────────────         ──────────────         ──────────────
  Extracción             Análisis               Revisión
  automática             con Copilot            y entrega
                                                
  python                 Pegar                  Verificar
  run_analysis.py        COPILOT_PROMPT.md      correcciones v3
  "archivo.twx"          en Copilot CLI         y entregar
                         + skill                al equipo Appian
                         profuturo-twx          
                                                
  ⚡ ~10 min             ⏱ ~2h 30min            🔍 ~15 min
```

**Total: ~2h 45min** vs. ~16h manuales → **ahorro: ~14 horas por proceso**

---

## 8 Ciclos de la Metodología v3

| Ciclo | Sección del reporte | Fuente de datos | Con suite | Manual |
|---|---|---|---|---|
| C1 | Estructura TWX · Inventario | `01_analyze.json` | ~10 min | ~~1.5h~~ |
| C2 | Constantes y variables de entorno | `62.*.xml` | ~15 min | ~~2h~~ |
| C3 | Lógica de negocio · Scripts JS | `08_scripts.txt` | ~20 min | ~~3h~~ |
| C4 | Interfaz · Botones de pantallas HHS | `64.*.xml` (Coach Views) | ~15 min | ~~2h~~ |
| C5 | Servicios de integración · IS | `03_services.json` | ~20 min | ~~2.5h~~ |
| C6 | Modelo de datos · Business Objects | `02_entities.json` | ~15 min | ~~1.5h~~ |
| C7 | UCAs y eventos asincrónicos | `04.*.xml` | ~10 min | ~~1h~~ |
| C8 | Flujos BPD · Diagrama completo | `06_flows.txt` | ~25 min | ~~3h~~ |
| | **TOTAL** | | **~2h 10min** | ~~**16h 30min**~~ |

---

## Capacidades detalladas

### 🏗️ Inventario completo de artefactos
- Clasifica los artefactos del TWX en 8 tipos por prefijo XML
- Identifica el nombre de la aplicación desde el BPD principal (no del MANIFEST, que no contiene datos útiles en IBM BPM)
- **Comandos:** `analyze` → `01_analyze.json`

### 🗄️ Business Objects completos
- Extrae todos los Business Objects con campos, tipos de dato, herencia y namespace
- Base para el modelo de datos en Appian
- **Comandos:** `entities` → `02_entities.json`

### ⚙️ Servicios clasificados IS / GSS / HHS
- Extrae servicios con pasos, scripts JavaScript, inputs/outputs
- Distingue automáticamente Integration Services (`processType=4`), General System Services (`6`) y Human-facing Services (`3`)
- **Comandos:** `services` → `03_services.json`

### 🔀 Flujos con orden real
- Genera diagramas Mermaid flowchart usando `<sequenceFlow>` para el orden real
- **Nunca** usa coordenadas X/Y que darían orden incorrecto
- **Comandos:** `flows` → `06_flows.txt`

### 📜 Scripts JavaScript embebidos
- Extrae todo el JavaScript embebido en servicios y BPDs
- Etiquetado por artefacto y paso — base para el análisis de lógica de negocio
- **Comandos:** `scripts` → `08_scripts.txt` (455 KB)

### 🌐 Endpoints REST / SOAP
- Detecta todas las URLs externas usadas en los Integration Services
- Identifica dependencias con sistemas externos para la migración a Appian
- **Comandos:** `endpoints` → `07_endpoints.txt`

### 🔗 Grafo de dependencias
- Genera grafo Mermaid de dependencias entre servicios, UCAs, BPDs y Business Objects
- Identifica qué componentes son bloqueantes para la migración
- **Comandos:** `deps` → `05_deps.txt`

### 📖 Documentación Markdown completa
- 378 KB de documentación unificada que describe todos los artefactos
- Sirve como base de conocimiento técnico incluida en el prompt maestro
- **Comandos:** `docs` → `09_docs.md`

### 🤖 Prompt maestro para Copilot CLI
- `COPILOT_PROMPT.md` (57 KB) con todos los datos + instrucciones v3 por ciclo
- Solo hay que pegarlo en Copilot CLI con el skill `profuturo-twx` activado
- **Generado por:** `run_analysis.py`

---

## Caso real validado: Profuturo Redención de Bono

**TWX:** `Profuturo_Redencion_Bono_AP · v1.17.51` · 24.2 MB · IBM BPM → Appian

TWX de producción que implementa el flujo completo de Redención de Bono para Profuturo, incluyendo integración con sistemas UDI, generación de archivos de respuesta y gestión de tareas humanas.

**Resultado de la suite:**
- ✅ 9/9 comandos CLI exitosos
- ✅ 232 artefactos extraídos y clasificados
- ✅ 57 KB de prompt maestro generado
- ✅ 11 correcciones v3 aplicadas

### ⚠️ Correcciones críticas solo presentes en la Metodología v3

| # | Corrección | Impacto sin ella |
|---|---|---|
| 1 | Orden de pasos por `sequenceFlow`, nunca por X/Y | Flujo documentado en orden incorrecto |
| 2 | Botones de HHS desde `64.*.xml` (Coach Views) | Botones incorrectos o incompletos |
| 3 | `PostponeAction` = "Cerrar tarea en Appian" | Acción documentada como Posponer/Cancelar |
| 4 | IS "IG Revisión UDI" = SÍNCRONO (no hay nodo UCA) | Flujo de integración documentado erróneo |
| 5 | Variables de entorno en `62.*.xml`, no en manifest | Variables `tw.env.*` perdidas en el análisis |
| 6 | ID `8627` Dev/Test/Stage · `8628` en Producción | Error crítico en ambiente de producción |

---

## ROI y justificación

### ✅ Con la Suite NTT DATA

- ✓ **Análisis reproducible** — mismo resultado en cada ejecución
- ✓ **Sin dependencia de IBM Designer** — corre en cualquier máquina con Python
- ✓ **Escalable a múltiples TWX** — mismo proceso para cada proceso IBM BPM
- ✓ **Metodología documentada** — el skill `profuturo-twx` es reutilizable
- ✓ **11 correcciones v3 siempre aplicadas** — no depende de la memoria del analista
- ✓ **Integración nativa con Copilot CLI** — workflow moderno y auditable
- ✓ **Output estructurado (JSON + MD)** — integrable con otras herramientas
- ✓ **Onboarding de nuevo analista en horas** — instrucciones paso a paso en el skill

### ✗ Sin la Suite — Manual

- ✗ **16+ horas por proceso** — inviable para proyectos con decenas de TWX
- ✗ **Requiere IBM Designer** — licencia, versión, acceso al servidor BPM
- ✗ **Errores de interpretación frecuentes** — orden incorrecto, botones equivocados
- ✗ **No reproducible** — cada analista documenta diferente
- ✗ **Correcciones v3 no aplicadas** — el analista no sabe qué no sabe
- ✗ **Sin historial** — si el analista se va, el conocimiento se va con él
- ✗ **Output no estructurado** — documentos Word/Excel difíciles de procesar
- ✗ **Onboarding lento** — semanas para que un nuevo analista sea productivo

---

## Inicio rápido — 4 comandos

```bash
# 1. Ir al directorio del proyecto
cd "~/Documents/NTTDATA-IBM-TWX-Suite"

# 2. Copiar tu TWX a la carpeta de muestras
cp "MiApp.twx" 05_muestras_twx/

# 3. Ejecutar el pipeline completo
python run_analysis.py "05_muestras_twx/MiApp.twx"

# 4. Abrir COPILOT_PROMPT.md en Copilot CLI con skill profuturo-twx
```

**Output generado en `output/{nombre_twx}/`:**

| Archivo | Tamaño | Contenido |
|---|---|---|
| `01_analyze.json` | ~0.5 KB | Inventario de 232 artefactos por tipo |
| `02_entities.json` | ~10 KB | 54 Business Objects |
| `03_services.json` | ~23 KB | 74 servicios IS/GSS/HHS |
| `06_flows.txt` | ~8 KB | Diagramas Mermaid |
| `08_scripts.txt` | ~455 KB | JavaScript extraído |
| `09_docs.md` | ~378 KB | Documentación completa |
| `COPILOT_PROMPT.md` | ~57 KB | ⭐ Prompt maestro para Copilot |
| `xml_extracts/` | 224 XMLs | Clasificados por prefijo |

---

*NTT DATA · IBM TWX Reverse Engineering Suite · v1.0.0 · Metodología v3*  
*llopezdo@emeal.nttdata.com · IBM Integration Services · Legacy Migration · EMEAL*  
*© 2026 NTT DATA*
