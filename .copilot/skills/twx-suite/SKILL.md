---
name: twx-suite
description: >
  Complete reverse engineering suite for IBM Integration Designer / IBM BPM
  .twx files. Use this skill when the user wants to do a full analysis, reverse
  engineer a TWX file, migrate from IBM BPM/BAW, or run multiple analysis
  cycles on a TWX package. This is the master skill that orchestrates all
  individual TWX analysis capabilities.
allowed-tools: shell
---

## twx-suite — Complete TWX Reverse Engineering Suite

**NTTDATA IBM TWX Reverse Engineering Suite v1.0.0**

This skill provides access to all 9 analysis capabilities for IBM Integration
Designer / IBM BPM `.twx` files.

### Tools package location
`C:\Users\llopezdo\OneDrive - NTT DATA EMEAL\Documentos\NTTDATAIBMTWXSuite\NTTDATA-IBM-TWX-Suite\01_herramientas_python`

All commands run as:
```
python -m ibm_twx_tools <command> "<path_to_file.twx>" [options]
```

### Available cycles (commands)

| Cycle | Command | Description |
|-------|---------|-------------|
| 1. Analyze | `analyze` | Full summary: app name, version, artifact counts by type |
| 2. Entities | `entities` | Business Objects, data models, field definitions |
| 3. Services | `services` | Services, steps, inputs/outputs, dependencies |
| 4. Flows | `flows` | Mermaid flowchart diagrams per process/service |
| 5. Deps | `deps` | Dependency call graph (Mermaid) |
| 6. Docs | `docs` | Complete Markdown documentation (all of the above) |
| 7. Scripts | `scripts` | All embedded JavaScript/Groovy code |
| 8. Endpoints | `endpoints` | External REST/SOAP/HTTP endpoints |
| 9. Entries | `entries` | Entry points — uncalled artifacts (public API) |

### How to use
When asked about a .twx file, determine which cycle(s) are needed:

- **"What is in this TWX?"** → run `analyze` first, then offer the other cycles
- **"Document this application"** → run `docs` with output file
- **"Show me the architecture"** → run `analyze` + `deps` + `entries`
- **"Help me migrate this"** → run full sequence: analyze → entities → services → flows → deps → endpoints → entries → docs
- **"Show me the integrations"** → run `endpoints` + `services`
- **"What code is embedded?"** → run `scripts`

### Full reverse engineering workflow
For a complete reverse engineering session, run in this order:

```
# Step 1: Overview
python -m ibm_twx_tools analyze "<file.twx>"

# Step 2: Data model
python -m ibm_twx_tools entities "<file.twx>"

# Step 3: Services & logic
python -m ibm_twx_tools services "<file.twx>"

# Step 4: Process flows
python -m ibm_twx_tools flows "<file.twx>"

# Step 5: Dependencies
python -m ibm_twx_tools deps "<file.twx>"

# Step 6: External integrations
python -m ibm_twx_tools endpoints "<file.twx>"

# Step 7: Embedded scripts
python -m ibm_twx_tools scripts "<file.twx>"

# Step 8: Public API surface
python -m ibm_twx_tools entries "<file.twx>"

# Step 9: Full documentation
python -m ibm_twx_tools docs "<file.twx>" -o "<output>.md"
```

### Important notes
- `.twx` files are ZIP archives containing XML artifacts
- Supported artifact types: business_process (.bpd), service (.service),
  business_object (.bo), decision_table (.decision), human_task (.htm),
  event_subprocess (.epa), web_service (.web), integration_service (.integr)
- IBM namespaces: lombardi 8.0, bpd, svc, bo, dec, baw 20.0
- All output is in JSON (analyze/entities/services/endpoints/entries) or
  plain text with Mermaid blocks (flows/deps/scripts)
