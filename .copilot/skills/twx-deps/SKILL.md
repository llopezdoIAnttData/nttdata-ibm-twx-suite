---
name: twx-deps
description: >
  Builds a dependency call graph between all artifacts in an IBM .twx file.
  Use when the user asks about dependencies, which services call which, the
  call graph, inter-service relationships or impact analysis of a TWX package.
allowed-tools: shell
---

## twx-deps — Build Dependency Call Graph

When asked about dependencies, call graph, which artifact calls which, or
impact analysis of a .twx file, run:

```
python -m ibm_twx_tools deps "<path_to_file.twx>"
```

Run from cwd:
`C:\Users\llopezdo\OneDrive - NTT DATA EMEAL\Documentos\NTTDATAIBMTWXSuite\NTTDATA-IBM-TWX-Suite\01_herramientas_python`

### Steps
1. Confirm the .twx file path.
2. Run: `python -m ibm_twx_tools deps "<twx_path>"`
3. The output is a Mermaid `graph LR` diagram showing caller → callee relationships.
4. Present it wrapped in a ```mermaid code block.
5. Analyze the graph and add commentary:
   - Which artifacts have the most dependents (are most critical)
   - Which artifacts have no callers (potential entry points or orphans)
   - Identify circular dependency patterns if any
   - Flag external service calls (references not found in the package)

### Edge labels
Each arrow is labeled with the relationship type:
- `serviceRef` — direct service call
- `calledElement` — BPD subprocess call
- `calledService` — service invocation
- `processRef` — process reference
