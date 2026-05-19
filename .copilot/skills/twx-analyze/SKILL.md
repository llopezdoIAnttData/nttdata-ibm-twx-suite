---
name: twx-analyze
description: >
  Full summary analysis of an IBM Integration Designer / IBM BPM .twx file.
  Use this skill when the user asks to analyze, summarize, inspect or get an
  overview of a .twx file. Returns JSON with app name, version, toolkit flag
  and artifact counts by type.
allowed-tools: shell
---

## twx-analyze — Full Analysis of a .twx File

When asked to analyze or summarize a .twx file, run:

```
python -m ibm_twx_tools analyze <path_to_file.twx>
```

The tools package is located at:
`C:\Users\llopezdo\OneDrive - NTT DATA EMEAL\Documentos\NTTDATAIBMTWXSuite\NTTDATA-IBM-TWX-Suite\01_herramientas_python`

Run the command from that directory (use `cwd` parameter), or ensure the
package is installed (`pip install -e .` was run in that folder).

### Steps
1. Confirm the .twx file path exists.
2. Run: `python -m ibm_twx_tools analyze "<twx_path>"`
   from cwd: `C:\Users\llopezdo\OneDrive - NTT DATA EMEAL\Documentos\NTTDATAIBMTWXSuite\NTTDATA-IBM-TWX-Suite\01_herramientas_python`
3. Parse the JSON output and present it in a readable table to the user.
4. Summarize: app name, version, whether it is a toolkit, total artifacts, and
   a breakdown by artifact type (business_process, service, business_object, etc.).

### Output example
```json
{
  "app_name": "MyApp",
  "app_version": "1.0",
  "toolkit": false,
  "total_artifacts": 42,
  "by_type": {
    "business_process": 5,
    "service": 18,
    "business_object": 12,
    "decision_table": 3,
    "human_task": 4
  }
}
```
