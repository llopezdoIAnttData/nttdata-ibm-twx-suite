---
name: profuturo-twx
description: >
  Specialized knowledge for analyzing Profuturo IBM BPM TWX files and migrating
  to Appian. Use this skill when working with Profuturo, Redención de Bono,
  MP Redencion, Profuturo_Redencion_Bono_AP or any Profuturo IBM BPM project.
  Contains the complete extraction methodology (v3), correction history, and
  IBM BPM → Appian migration patterns.
allowed-tools: shell
---

# Profuturo — IBM BPM TWX Extraction & Migration Knowledge (v3)

**Proyecto:** MP Redención de Bono — Profuturo Fase 3 GenAI
**Fuente:** `Profuturo_Redencion_Bono_AP v1.17.51.twx`
**Destino:** Appian (reimplementación, NO migración 1:1)
**Metodología:** ExtracciónTécnica v3 (18 mayo 2026, NTT DATA)

---

## Taxonomía del TWX — Prefijos y artefactos

| Prefijo | Artefacto IBM | Cantidad | Cómo identificarlo |
|---------|--------------|----------|-------------------|
| `1.*` | Servicios (HHS + IS + GSS) | ~72 | `processType` en el XML |
| `4.*` | UCAs (Undercover Agents) | ~15 | `schedType`, `schedEvent` |
| `12.*` | Business Objects | ~54 | `twClass`, `fields` |
| `25.*` | BPDs (procesos) | ~44 | `BPD`, `lane`, `sequenceFlow` |
| `64.*` | Coach Views (UI) | ~39 | `boundaryEvent`, `postponeAction` |
| `manifest.xml` | Constantes y metadatos | 1 | `environmentVariables` |

### Subtipos de servicios (prefijo `1.*`)
Distinguir por `processType`:
- `processType=3` → **HHS** (Human Service — pantallas de usuario)
- `processType=4` → **IS** (Integration Service — llamadas a IIB/WS)
- `processType=6` → **GSS** (General System Service — automáticos)

---

## Pipeline de extracción v3 — 8 ciclos

### Ciclo 1 — Exploración de estructura TWX
**Archivo:** el TWX como ZIP
**Output:** inventario por prefijo + identificación del BPD principal
- Listar todos los archivos XML del ZIP
- Agrupar por prefijo numérico
- Leer 1 archivo de muestra por prefijo para identificar artefacto IBM

### Ciclo 2 — Constantes de entorno (`tw.env.*`)
**Archivo:** `manifest.xml` → sección `<environmentVariables>`
**Output:** Sección 1 — 71 constantes por categoría y ambiente
- Categorías: HOST_PUERTO, IDs proceso/subproceso/estado, IDs subetapa, plantillas notificación, URLs REST
- ⚠️ **Crítico Profuturo:** `ID_SUBETAPA_GENERACION_ARCHIVO_RESPUESTA_81` es **8627** en Dev/Test/Stage pero **8628** en Prod

### Ciclo 3 — Integration Services (IS) con payloads SOAP
**Archivo:** `1.*.xml` donde `processType=4`
**Output:** Secciones 2 (endpoints) y 3 (payloads INPUT/OUTPUT)
- Para cada IS: nombre, operación WSDL, URL patrón, campos INPUT (`nombre/tipo/tw.local.*`), campos OUTPUT, fault types
- Clasificar como **SYNC** si el BPD continúa directamente después del IS
- Clasificar como **ASYNC** si el proceso espera en un UCA antes de continuar
- ✅ **Corrección v3:** IS "IG Revisión UDI" = **SÍNCRONO** (el BPD pasa directamente al GSS "Respuesta RevisionUDI GS" sin nodo UCA intermedio)

### Ciclo 4 — Acciones de usuario desde Coach Views (botones)
**Archivo:** `64.*.xml` (Coach Views)
**Output:** Sección 4 — 105 botones de 21 HHS
- Cada `<boundaryEvent>` en el XML de un Coach = un botón real
- El `<postponeAction>` = botón especial
- ✅ **Corrección crítica v3:** `PostponeAction` = **"Cerrar tarea en Appian"** (NO Posponer, NO Cancelar)
- ⚠️ `tw.options.nombreBoton` = botón dinámico, implementar en Appian con expresión en propiedad `label`
- ❌ **Error v1/v2:** inferían botones desde descripciones de HHS — incorrecto. Los botones viven en los archivos `64.*`

### Ciclo 5 — UCAs con correlación de datos
**Archivo:** `4.*.xml` + BPDs que los invocan (`25.*.xml`)
**Output:** Sección 7 — 15 UCAs con correlación completa
- Para cada UCA: `schedEvent` (cola BUS que lo activa), `linkedService`, BPD/sub-proceso donde reanuda
- **Correlación de datos:** campos de la respuesta BUS → `tw.local.*` del proceso
- **Decisión posterior:** gateway inmediatamente después del UCA y sus condiciones
- Campos clave de correlación Profuturo: `folio`, `exitoso`, `identificados100`, `mensaje` → `tw.local.*`

### Ciclo 6 — GSS en orden real por sequenceFlow
**Archivo:** `1.*.xml` donde `processType=6`
**Output:** Sección 8 — 22 GSS con pasos ordenados
- ✅ **Corrección v3:** construir grafo siguiendo `<sequenceFlow>` desde `startEvent` hasta `ExitPoint`
- ❌ **Error v1/v2:** orden de aparición en XML ≠ orden de ejecución
- **Patrón común Profuturo (12 de 22 GSS):**
  1. Mapeo Entrada → 2. Validar Parámetros → 3. ¿datos válidos? → 4. Invocar UCA → 5. Datos de Salida → 6. Finalizar

### Ciclo 7 — Tabla de decisiones (gateways)
**Archivo:** `25.*.xml` (BPDs principales) → `exclusiveGateway` + `conditionExpression`
**Output:** Sección 6 — tabla de decisiones + scripts JS
- Variables de decisión clave en Profuturo:
  - `tw.local.salida` (0-3) → acción en SP Confirmación Movimientos
  - `tw.local.exitoso` (bool) → éxito/fallo de cada servicio
  - `tw.local.esAcreditacion` (bool) → flujo alternativo acreditación vs devolución
  - `tw.local.finalizarFlujo` (bool) → terminar el proceso
  - `tw.local.existeNoRechazados` (bool) → hay registros pendientes
  - `tw.local.rechazarFolio` (bool) → rechazar el folio completo

### Ciclo 8 — Mapeo BUS/MQ → NOV_INSTANCE_MANAGEMENT
**Archivos:** `NOV_INSTANCE_MANAGEMENT.sql` + `_ucas.json` + constantes
**Output:** Sección 10 — mapeo campo-a-campo + flujo Appian documentado
- **Patrón IBM:** IS → BUS message → IIB → GSS Respuesta → InvokeUCA → BPD reanuda
- **Patrón Appian (NOV_INSTANCE_MANAGEMENT):**
  - INSERT al llamar el IS
  - UPDATE IS_ACTIVE=0 cuando IIB responde
  - El proceso Appian reacciona al cambio de `STATUS_ID`
- Mapeo: `tw.local.salida` → `ACTION_OUT`, `tw.local.exitoso` → `STATUS_ID`, `tw.local.mensaje` → `RESPONSE_OUT`

---

## Reglas críticas de extracción (aprendizajes v1→v3)

1. **Orden de pasos:** SIEMPRE usar `sequenceFlow` — nunca orden XML ni coordenadas X/Y
2. **Botones de HHS:** SIEMPRE desde `64.*.xml` (Coach Views) — nunca desde descripciones
3. **PostponeAction:** = "Cerrar tarea" en Appian (no Posponer)
4. **Clasificación IS sync/async:** verificar en el BPD si hay nodo UCA entre el IS y el siguiente paso
5. **Constantes por ambiente:** siempre comparar DEV vs PROD — pueden diferir (ej: `ID_SUBETAPA_GENERACION_ARCHIVO_RESPUESTA_81`)
6. **laneId:** para asignar actividades a perfiles, leer atributo `laneId` de cada actividad en el BPD
7. **Migración NO es 1:1:** documentar "qué hay en IBM", NO recomendar equivalencias directas

---

## Cómo ejecutar el análisis con las herramientas Python

```bash
# Ejecutar desde:
cd "C:\Users\llopezdo\OneDrive - NTT DATA EMEAL\Documentos\NTTDATAIBMTWXSuite\NTTDATA-IBM-TWX-Suite\01_herramientas_python"

# Ciclo 1: Exploración
python -m ibm_twx_tools analyze "ruta/al/archivo.twx"

# Ciclo 2+3: BOs + Servicios
python -m ibm_twx_tools entities "ruta/al/archivo.twx"
python -m ibm_twx_tools services "ruta/al/archivo.twx"

# Ciclo 6: Flujos con orden correcto
python -m ibm_twx_tools flows "ruta/al/archivo.twx"

# Ciclo 7: Dependencias
python -m ibm_twx_tools deps "ruta/al/archivo.twx"

# Ciclos 4+5: Scripts embebidos y endpoints
python -m ibm_twx_tools scripts "ruta/al/archivo.twx"
python -m ibm_twx_tools endpoints "ruta/al/archivo.twx"

# Puntos de entrada
python -m ibm_twx_tools entries "ruta/al/archivo.twx"

# Documentación completa
python -m ibm_twx_tools docs "ruta/al/archivo.twx" -o "salida.md"
```

---

## Ciclo 10 — Mapeo F3: Arquitectura de Procesos Efímeros (25 mayo 2026)

> **CRÍTICO:** La migración IBM BPM → Appian Fase 3 NO usa procesos long-lived.
> Cada BPD se descompone en N+1 procesos efímeros. Leer esta sección antes de generar cualquier Process Model.

### Comando

```bash
python -m ibm_twx_tools parametria "ruta/al/archivo.twx" -o "09_parametria_f3.json"
```

### Clasificación de Business Objects para F3

En F3 no hay proceso padre que cargue un BO en memoria entre pasos. La categoría determina qué artefacto Appian se genera:

| Categoría | Criterio de detección | Destino Appian |
|-----------|----------------------|----------------|
| **domain_entity** | Tiene campo `identificador`/`folio`, O referenciado en correlación UCA, O >10 campos | Record Type con tabla `NOV_*` en BD |
| **dto** | Solo aparece en inputs/outputs de IS (payload request/response) | CDT o variable local del proceso efímero |
| **catalog** | Nombre contiene "Catalogo", "Tipo", "Estatus", "Siefore", etc. | Skip — tabla catálogo existente o Constant |

**Ejemplos Profuturo:**
- `ArchivoBO` (24 usos, campos: identificador, folio, folioSubSecuente, +18) → **domain_entity** → `NOV Archivo Main` Record Type
- `ETLGenericRequest` (request IS) → **dto** → variable local
- `CatalogoBO` (id, valor, descripcion) → **catalog** → tabla catálogo existente

### Descomposición de BPDs en procesos efímeros F3

**Regla:** Para cada BPD con N puntos async (IS → UCA), F3 genera N+1 procesos lanzadores + 1 `NOV Respuesta Bus` compartido.

Un "punto de corte F3" ocurre cuando en el `sequenceFlow` un `serviceTask`/`integrationTask` es seguido de un `intermediateEvent` (espera UCA).

**Ejemplo: MP Redención de Bono (3 puntos async → 4 procesos + 1 respuesta-bus):**

| Paso | Proceso F3 | IS IBM que lanza | UCA que esperaba |
|------|------------|-----------------|-----------------|
| 1 | `NOV MPRedencionBono Paso1` | IG Validar Solicitud | UCA Respuesta Validar |
| 2 | `NOV MPRedencionBono Paso2` | IG Acreditar Bono | UCA Respuesta Acreditar |
| 3 | `NOV MPRedencionBono Paso3` | IG Confirmar Operación | UCA Respuesta Confirmar |
| 4 | `NOV MPRedencionBono Finalizar` | (cierre) | (ninguno) |
| Shared | `NOV Respuesta Bus Redencion` | (disparado por IIB response) | — |

### Campos NOV_INSTANCE_MANAGEMENT

Variables IBM que "cruzan" un punto async (seteadas en paso N, leídas en paso N+1) DEBEN persistir en la tabla `NOV_INSTANCE_MANAGEMENT`:

| Variable IBM | Campo Appian | Tipo | Por qué persiste |
|-------------|-------------|------|-----------------|
| `tw.local.salida` | `ACTION_OUT` | Integer | Decisión del gateway post-respuesta |
| `tw.local.exitoso` | `STATUS_ID` | Boolean | Indicador éxito/fallo del IS |
| `tw.local.folio` | `FOLIO` | Text | Identificador principal del proceso |
| `tw.local.folioSubSecuente` | `FOLIO_SUBSECUENTE` | Text | Folio derivado |
| `tw.local.esAcreditacion` | `ES_ACREDITACION` | Boolean | Flujo alternativo |
| `tw.local.finalizarFlujo` | `FINALIZAR_FLUJO` | Boolean | Señal de cierre |
| `tw.local.existeNoRechazados` | `EXISTE_NO_RECHAZADOS` | Boolean | Control de pendientes |
| `tw.local.rechazarFolio` | `RECHAZAR_FOLIO` | Boolean | Acción de rechazo |
| `tw.local.opcionIDC` | `ACCION_IDC` | Text | Decisión IDC (Fase 3 Traspasos) |

### Template de parametría (tabla BD)

La tabla de parametría gobierna "dado mi estado actual, cuál es el siguiente proceso F3":

```json
{
  "proceso": "MP Redencion Bono",
  "pasos": [
    {
      "id_paso": 1,
      "proceso_appian": "NOV MPRedencionBono Paso1",
      "integracion_is": "IG Validar Solicitud Redencion",
      "salidas": [
        {"condicion": "STATUS_ID=true AND ACTION_OUT=0", "siguiente_paso": 2},
        {"condicion": "STATUS_ID=false", "siguiente_paso": -1, "accion": "error"}
      ]
    }
  ]
}
```

### Regla 8 (corrección v3 → F3): Pattern async actualizado

**Antes (F2 long-lived):**
> IS → BUS → IIB → UCA → BPD reanuda (proceso sigue en RAM)

**Ahora (F3 efímero):**
> IS → BUS → IIB → NOV_INSTANCE_MANAGEMENT UPDATE (IS_ACTIVE=0) → NOV Respuesta Bus lee parametría → lanza NUEVO proceso efímero Paso(N+1)

El proceso padre NO reanuda. Termina en el momento en que llama al IS. Un proceso nuevo (disparado por `NOV Respuesta Bus`) recoge la respuesta y decide el siguiente paso usando la tabla de parametría.

---

## Artefactos de referencia disponibles

La arquitectura de conocimiento completa de la extracción v3 está documentada en:
`~/.copilot/skills/profuturo-twx/ArquitecturaConocimiento_v1.html`

Este archivo HTML contiene:
- Estructura completa del TWX de Profuturo Redención de Bono
- Los 8 prompts ejecutados con inputs y outputs
- Las 11 correcciones de la retro del equipo
- La evolución v1 → v2 → v3
- El mapa completo de conocimiento (entradas → procesamiento → salidas)
