---
name: twx-entries
description: >
  Identifies entry points in an IBM .twx file — artifacts (processes, services)
  that are not called by any other artifact and therefore represent the public
  API or top-level triggers of the application. Use when the user asks about
  entry points, top-level processes, public APIs, triggers or uncalled artifacts.
allowed-tools: shell
---

## twx-entries — Find Entry Points (Public API)

When asked about entry points, top-level processes, uncalled artifacts or the
public API surface of a .twx file, run:

```
python -m ibm_twx_tools entries "<path_to_file.twx>"
```

Run from cwd:
`C:\Users\llopezdo\OneDrive - NTT DATA EMEAL\Documentos\NTTDATAIBMTWXSuite\NTTDATA-IBM-TWX-Suite\01_herramientas_python`

### Steps
1. Confirm the .twx file path.
2. Run: `python -m ibm_twx_tools entries "<twx_path>"`
3. Parse the JSON array.
4. Present as a table:
   | Artifact Name | Type | Path in TWX |
5. Group by artifact type (business_process, service, integration_service, etc.)
6. Explain the significance of each group:
   - Business processes = end-to-end workflows triggered by users or events
   - Services = utility operations called programmatically
   - Integration services = external system connectors

### What entry points tell us
Entry points are artifacts with no callers within the package. They represent:
- The public API surface of the application
- Starting points for migration analysis
- Candidate endpoints for new API definitions (REST/GraphQL)
- Human task entry points that need UI migration
