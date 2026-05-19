---
name: twx-services
description: >
  Extracts services, integration services, human tasks and their internal steps,
  inputs/outputs and logic from an IBM .twx file. Use when the user asks about
  services, operations, APIs, integrations or service logic in a TWX package.
allowed-tools: shell
---

## twx-services — Extract Services & Logic

When asked about services, steps, operations, inputs/outputs or service logic
in a .twx file, run:

```
python -m ibm_twx_tools services "<path_to_file.twx>"
```

Run from cwd:
`C:\Users\llopezdo\OneDrive - NTT DATA EMEAL\Documentos\NTTDATAIBMTWXSuite\NTTDATA-IBM-TWX-Suite\01_herramientas_python`

### Steps
1. Confirm the .twx file path.
2. Run: `python -m ibm_twx_tools services "<twx_path>"`
3. Parse the JSON array.
4. For each service present:
   - Name, type (General Service / Integration Service / Web Service / Human Task)
   - Description
   - Inputs table (name, type, required)
   - Outputs table (name, type)
   - Steps table (step number, name, type, called service if any)
   - Dependencies (other services called)
5. Group services by type. Highlight integration services and their external dependencies.

### Service types handled
- General Service
- Integration Service
- Web Service
- Human Task (human approval workflows)
