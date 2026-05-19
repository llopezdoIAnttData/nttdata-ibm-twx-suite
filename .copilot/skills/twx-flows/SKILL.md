---
name: twx-flows
description: >
  Generates Mermaid flowchart diagrams for all processes and services inside an
  IBM .twx file. Use when the user asks to visualize flows, process diagrams,
  flowcharts or the execution path of a TWX process or service.
allowed-tools: shell
---

## twx-flows — Generate Mermaid Process Flow Diagrams

When asked to visualize flows, diagrams, process maps or execution paths from
a .twx file, run:

```
python -m ibm_twx_tools flows "<path_to_file.twx>"
```

Run from cwd:
`C:\Users\llopezdo\OneDrive - NTT DATA EMEAL\Documentos\NTTDATAIBMTWXSuite\NTTDATA-IBM-TWX-Suite\01_herramientas_python`

### Steps
1. Confirm the .twx file path.
2. Run: `python -m ibm_twx_tools flows "<twx_path>"`
3. The output contains one Mermaid `flowchart TD` block per process/service.
4. Present each diagram wrapped in a ```mermaid code block.
5. Add a title heading for each diagram with the process name and artifact type.
6. If there are many flows (> 5), list their names first and ask the user if
   they want all or specific ones.

### Node types in diagrams
- `((...))` = Start event
- `(((...)))` = End event
- `{...}` = Gateway (decision)
- `[/..../]` = Script task
- `[...]` = Regular task / service call
- `-->` = Normal flow
- `-.->` = Error path
