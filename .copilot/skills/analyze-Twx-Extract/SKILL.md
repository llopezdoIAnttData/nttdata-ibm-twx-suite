---
name: analyze-Twx-Extract
description: >
  IBM BPM TWX complete extraction and HTML report generation.
  Use this skill when the user types /analyze-Twx-Extract or asks to analyze
  a TWX file, extract IBM BPM artefacts, or generate a technical extraction
  report. Shows the NTT DATA banner, asks for the TWX file path, runs all
  9 analysis cycles, extracts XMLs, and generates a navigable HTML report.
allowed-tools: shell
---

## analyze-Twx-Extract — IBM TWX Extracción Completa

**NTTDATA IBM TWX Reverse Engineering Suite v1.0.0**

Este skill ejecuta el pipeline completo de extracción sobre un archivo `.twx`
de IBM BPM / IBM BAW y genera un reporte HTML navegable con toda la
arquitectura técnica del proceso.

---

### Cómo se invoca

El usuario ejecuta `/analyze-Twx-Extract` en GitHub Copilot CLI.

---

### Instrucciones de ejecución

Cuando este skill se activa, ejecuta los siguientes pasos **en orden**:

#### PASO 1 — Mostrar banner y pedir path

Ejecuta el pipeline en modo interactivo:

```bash
cd "C:\Users\llopezdo\OneDrive - NTT DATA EMEAL\Documentos\NTTDATAIBMTWXSuite\NTTDATA-IBM-TWX-Suite"
python run_analysis.py
```

Si `run_analysis.py` no es accesible, usar la ruta instalada:

```bash
cd "$USERPROFILE\Documents\NTTDATA-IBM-TWX-Suite"
python run_analysis.py
```

El script:
1. Muestra el banner NTT DATA en la terminal
2. Pregunta: `📁 Ruta del archivo .TWX:`
3. El usuario pega la ruta (relativa o absoluta)
4. Ejecuta los 9 ciclos automáticamente con spinner animado
5. Extrae XMLs del ZIP
6. Genera `COPILOT_PROMPT.md`
7. **Genera el reporte HTML** `<nombre>_ExtraccionTecnica.html`

#### PASO 2 — Abrir el reporte HTML

Cuando finalice, abre el reporte HTML generado:

```powershell
# Buscar el HTML generado en la carpeta output
$htmlFiles = Get-ChildItem -Path ".\output" -Recurse -Filter "*_ExtraccionTecnica.html" | Sort-Object LastWriteTime -Descending | Select-Object -First 1
if ($htmlFiles) { Start-Process $htmlFiles.FullName }
```

#### PASO 3 — Confirmar al usuario

Muestra al usuario:
- Ruta del reporte HTML generado
- Ruta del COPILOT_PROMPT.md
- Instrucciones para profundizar el análisis con `profuturo-twx`

---

### Salida esperada

| Archivo | Descripción |
|---------|-------------|
| `01_analyze.json` | Resumen: conteo de artefactos por tipo |
| `02_entities.json` | Business Objects con campos y herencia |
| `03_services.json` | Servicios IS/GSS/HHS con pasos |
| `04_endpoints.json` | Endpoints externos (WSDL, URL) |
| `05_entries.json` | UCAs / Entry points con colas |
| `06_flows.txt` | Diagramas Mermaid de flujos |
| `07_deps.txt` | Grafo de dependencias |
| `08_scripts.txt` | Scripts JavaScript embebidos |
| `09_docs.md` | Documentación Markdown completa |
| `xml_extracts/` | XMLs por prefijo (1.*, 4.*, 12.*, 25.*, 64.*) |
| `COPILOT_PROMPT.md` | Prompt v3 listo para análisis profundo |
| `*_ExtraccionTecnica.html` | **Reporte HTML navegable — resultado principal** |

---

### Prefijos TWX (taxonomía crítica)

| Prefijo | Tipo | Subtipo |
|---------|------|---------|
| `1.*` | Servicios | processType 3=HHS, 4=IS, 6=GSS |
| `4.*` | UCAs | Undercover Agents |
| `12.*` | Business Objects | Entidades de datos |
| `25.*` | BPDs | Business Process Definitions |
| `62.*` | Variables de entorno | Dev / Prod |
| `64.*` | Coach Views | Componentes UI / Botones |

---

### Reglas metodología v3 (siempre aplicar)

1. Orden de pasos por `sequenceFlow`, NO por coordenadas X/Y
2. Botones extraídos de `64.*.xml`, NO de descripciones textuales
3. `PostponeAction` → mapear como "Cerrar tarea"
4. IG Revisión UDI → clasificar como SÍNCRONO
5. Variables de entorno desde `62.*.xml`, NO desde MANIFEST
6. ID entorno Dev ≠ ID entorno Prod (no confundir)
7. BOs documentados desde `12.*.xml`
8. UCAs correlacionan cola BUS → proceso BPD
9. Pasos GSS/HHS en orden real del XML sequenceFlow
10. Coach Views con botones reales del XML 64.*
11. Patrones BUS/MQ → documentar mapeo campo a campo

---

### Notas de integración

- Requiere Python 3.9+ con `ibm_twx_tools` instalado
- Ruta por defecto: `%USERPROFILE%\Documents\NTTDATA-IBM-TWX-Suite`
- Salida: `output\<nombre_twx>\`
- El HTML se abre directamente en el navegador con `Start-Process`
