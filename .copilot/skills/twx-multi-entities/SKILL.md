---
name: twx-multi-entities
description: >
  Agentic cross-TWX data model analysis across N IBM BPM .twx files.
  The LLM extracts Business Objects from all TWX files using the Python tool,
  then performs AI-driven semantic analysis to identify shared/reusable BOs,
  structural and semantic clusters, consolidation opportunities, and toolkit
  candidates. Generates a complete HTML report written by the AI including
  narrative insights, reuse strategy, and a prioritized action plan.
  Use when the user wants to compare data models across multiple TWX packages
  with AI interpretation, not just mechanical matching.
allowed-tools: shell
---

# twx-multi-entities — Agentic Cross-TWX Data Model Analyzer

**NTTDATA IBM TWX Reverse Engineering Suite v1.0.0 — Modo Agentic**

Este skill es **completamente agentic**: el LLM extrae los datos crudos con la
herramienta Python y luego **analiza, interpreta y genera el HTML por sí mismo**,
añadiendo inteligencia semántica que va más allá del matching mecánico de nombres.

```
ARQUITECTURA AGENTIC
─────────────────────────────────────────────────────
  FASE 1  Python tool → extracción de datos crudos (JSON)
  FASE 2  LLM         → análisis semántico e interpretación IA
  FASE 3  LLM         → generación del reporte HTML completo
  FASE 4  Shell       → escritura del fichero + apertura en navegador
─────────────────────────────────────────────────────
```

---

## FASE 1 — RECOLECCIÓN DE DATOS

### Paso 1.1 — Preguntar al usuario

Si el usuario no ha proporcionado rutas de ficheros .twx, pregunta:

```
¿Cómo proporcionas los ficheros .twx?
  [A] Ruta a un directorio (escanea todos los .twx recursivamente)
  [B] Rutas individuales separadas por punto y coma (;)

¿Dónde guardar el reporte HTML?
  (Enter = misma carpeta que los TWX, fichero: cross_model_AI_report.html)
```

### Paso 1.2 — Localizar los ficheros .twx

Si el usuario indica un directorio, listar los ficheros con:

```powershell
Get-ChildItem -Path "<directorio>" -Recurse -Filter "*.twx" | Select-Object -ExpandProperty FullName
```

Muestra la lista al usuario y confirma antes de continuar.

### Paso 1.3 — Extraer datos de CADA fichero .twx

Para **cada fichero .twx** encontrado, ejecuta los dos comandos siguientes y
captura su salida JSON completa:

```powershell
# Metadatos del paquete (nombre de app, versión, conteo de artefactos)
cd "C:\Users\llopezdo\OneDrive - NTT DATA EMEAL\Documentos\NTTDATAIBMTWXSuite\NTTDATA-IBM-TWX-Suite\01_herramientas_python"
python -m ibm_twx_tools analyze "<ruta_fichero.twx>"

# Business Objects completos (nombre, campos, tipos, herencia)
python -m ibm_twx_tools entities "<ruta_fichero.twx>"
```

Almacena en memoria el JSON de `entities` y el JSON de `analyze` por cada fichero.
Avanza fichero a fichero, no todos en paralelo, para evitar desbordamiento de contexto.
Informa al usuario del progreso: `[1/N] Extrayendo: <nombre_fichero>.twx ...`

---

## FASE 2 — ANÁLISIS SEMÁNTICO POR IA

Una vez recolectados TODOS los datos, el LLM realiza el análisis completo.
**No ejecutes ningún comando Python en esta fase.** Todo el análisis lo hace el LLM.

### 2.A — Clasificación exacta (matching por nombre)
Identifica BOs cuyo `name` aparece en 2 o más ficheros TWX.
Para cada uno, compara campo a campo y determina si la definición es:
- **Idéntica** → apto para reusar sin cambios
- **Compatible** → mismos campos clave, diferencias menores (tipos, required)
- **Divergente** → misma etiqueta, definiciones muy distintas → posible conflicto semántico

### 2.B — Clusters semánticos (matching por significado)
El LLM busca BOs con **diferentes nombres** pero que representan el **mismo concepto**
de negocio. Indicios a considerar:
- Campos con nombres equivalentes (ej: `clienteId` / `customerId` / `idCliente`)
- Campos con tipos equivalentes aunque con distinto nombre
- Descripciones que sugieren el mismo dominio (ej: Persona, Afiliado, Usuario)
- Patrones de herencia comunes (varios BOs extienden la misma base)
Agrupa estos BOs en **Clusters Semánticos** y explica el razonamiento.

### 2.C — Candidatos a Toolkit Compartido
Lista los BOs que **deberían moverse a un toolkit común** porque:
- Aparecen idénticos en 3+ ficheros → duplicación innecesaria
- Son clusters semánticos con alta similitud → unificar en un BO canónico
- Son entidades de dominio genérico (Persona, Dirección, Fecha, Moneda, etc.)

Para cada candidato, propón:
- **Nombre canónico** recomendado
- **Campos unificados** (superset de todos los ficheros)
- **Ficheros que lo usan** (quiénes deben migrar a la versión canónica)

### 2.D — BOs únicos
Lista BOs que solo existen en un fichero y no tienen equivalente semántico
en los demás. Clasifícalos como:
- `DOMINIO_ESPECÍFICO` — lógico que sea único (ej: BO muy especializado)
- `CANDIDATO_TOOLKIT` — podría ser útil para otros pero aún no se comparte
- `LEGACY` — parece desactualizado o sin uso claro

### 2.E — Score de reutilización IA
Calcula y justifica un score global (0–100) basado en:
```
Score = (BOs_identicos × 1.0 + BOs_compatibles × 0.7 + clusters_semánticos × 0.5)
        ─────────────────────────────────────────────────────────────────────────────
                              total_BOs_distintos
× 100
```
Interpreta el score:
- 0–30: modelos muy divergentes, alto esfuerzo de integración
- 31–60: reutilización parcial posible, revisar clusters semánticos
- 61–80: buen nivel, candidatos claros a toolkit
- 81–100: modelos muy alineados, toolkit factible inmediatamente

### 2.F — Plan de acción priorizado
Genera una lista ordenada (Alta / Media / Baja prioridad) de acciones concretas:
- Qué BOs mover al toolkit primero
- Qué BOs necesitan refactoring antes de unificar
- Qué BOs mantener separados y por qué
- Qué conflictos de naming/tipado resolver

---

## FASE 3 — GENERACIÓN DEL REPORTE HTML

El LLM genera un fichero HTML completo, auto-contenido y profesional.
El HTML DEBE incluir las siguientes secciones y elementos:

### Estructura obligatoria del HTML

```
1. CABECERA
   - Banner NTT DATA (fondo #003087, texto blanco)
   - Título: "Cross-TWX AI Data Model Analysis Report"
   - Subtítulo: fecha, N ficheros analizados, score IA
   - Barra de navegación lateral con anclas a cada sección

2. RESUMEN EJECUTIVO (fondo suave, tarjetas de métricas)
   - Tarjetas: N ficheros · N BOs totales · Score IA · N candidatos toolkit
   - Párrafo de interpretación IA (narrativa, no solo números)

3. BOs COMPARTIDOS — ANÁLISIS EXACTO
   - Tabla por cada BO compartido: aparece en / definición / estado (idéntico/compatible/divergente)
   - Para los divergentes: tabla comparativa campo a campo, columnas = ficheros TWX

4. CLUSTERS SEMÁNTICOS (sección IA)
   - Fondo diferenciado (ej: índigo suave) para destacar que es análisis IA
   - Por cada cluster: nombre del grupo propuesto, miembros, razonamiento IA,
     BO canónico recomendado con campos unificados

5. CANDIDATOS A TOOLKIT
   - Lista de BOs recomendados con: nombre canónico, prioridad (badge color),
     ficheros que lo usarían, campos del BO unificado

6. BOs ÚNICOS POR FICHERO
   - Por fichero: tabla de BOs únicos con clasificación (DOMINIO_ESPECÍFICO /
     CANDIDATO_TOOLKIT / LEGACY) y breve justificación IA

7. PLAN DE ACCIÓN IA
   - Tabla priorizada: Prioridad | Acción | BOs afectados | Justificación
   - Alta (rojo), Media (naranja), Baja (verde)

8. MODELO COMPLETO POR FICHERO (colapsable)
   - Sección <details><summary> por cada fichero TWX
   - Tabla de todos sus BOs con campos completos

9. PIE DE PÁGINA
   - Generado por: NTTDATA IBM TWX Suite v1.0.0 — Análisis IA
   - Fecha y hora de generación
```

### Estilo del HTML

```css
/* Paleta NTT DATA */
--ntt-blue:   #003087;
--ntt-red:    #e8001c;
--ntt-light:  #f0f4f8;
--ntt-border: #dde3ea;

/* Fuente */
font-family: 'Segoe UI', system-ui, sans-serif;

/* Badges de prioridad */
Alta    → background: #fee2e2; color: #991b1b;
Media   → background: #fef3c7; color: #92400e;
Baja    → background: #dcfce7; color: #166534;

/* Badge IA */
background: #ede9fe; color: #5b21b6; (púrpura)
```

El HTML debe ser **auto-contenido** (sin dependencias externas, sin CDN).
Todos los estilos en `<style>` inline. Compatible con cualquier navegador moderno.

---

## FASE 4 — ESCRITURA Y APERTURA

### Paso 4.1 — Escribir el fichero HTML

```powershell
$outputPath = "<ruta_salida.html>"
$htmlContent = @'
<AQUÍ EL HTML COMPLETO GENERADO POR EL LLM>
'@
[System.IO.File]::WriteAllText($outputPath, $htmlContent, [System.Text.Encoding]::UTF8)
Write-Host "✅ Reporte guardado en: $outputPath"
```

> **IMPORTANTE**: Usa `[System.IO.File]::WriteAllText` para garantizar UTF-8
> sin BOM y evitar problemas con caracteres especiales en el HTML.

### Paso 4.2 — Abrir en el navegador

```powershell
Start-Process $outputPath
```

### Paso 4.3 — Resumen final en consola

Imprime al usuario:

```
╔══════════════════════════════════════════════════════╗
║  ✅  ANÁLISIS IA COMPLETADO                          ║
╠══════════════════════════════════════════════════════╣
║  Ficheros analizados  : N                            ║
║  BOs totales          : N                            ║
║  Score reutilización  : XX/100                       ║
║  Candidatos toolkit   : N                            ║
║  Clusters semánticos  : N                            ║
║  Reporte HTML         : <ruta>                       ║
╚══════════════════════════════════════════════════════╝
```

Luego presenta en texto un **párrafo ejecutivo** (3-5 líneas) con la
interpretación IA del conjunto de modelos analizado.

---

## Reglas del modo agentic

1. **La IA razona, no solo compara cadenas.** Un BO llamado `Cliente` y otro
   llamado `Afiliado` pueden ser el mismo concepto — el LLM debe evaluarlo.
2. **Justifica siempre.** Cada recomendación lleva una explicación de por qué.
3. **El HTML lo escribe el LLM**, no la herramienta Python. El Python solo
   provee los datos crudos (JSON).
4. **Progreso visible.** Informa al usuario en cada paso cuántos ficheros
   quedan por procesar.
5. **Si un fichero falla**, registra el error y continúa con los demás. Al
   final informa qué ficheros no se pudieron procesar y por qué.
6. **Ficheros grandes**: si un fichero tiene >50 BOs, prioriza los BOs que
   aparecen en otros ficheros y agrupa el resto por namespace.

---

## Notas técnicas

- Herramienta base: `python -m ibm_twx_tools`
- Directorio: `C:\Users\llopezdo\OneDrive - NTT DATA EMEAL\Documentos\NTTDATAIBMTWXSuite\NTTDATA-IBM-TWX-Suite\01_herramientas_python`
- Requiere Python 3.9+ con `ibm_twx_tools` instalado (`pip install -e .`)
- Mínimo 2 ficheros .twx para análisis cruzado significativo
- El reporte HTML generado es completamente standalone (sin Internet)
