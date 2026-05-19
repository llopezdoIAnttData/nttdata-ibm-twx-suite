---
name: twx-docs
description: >
  Generates complete Markdown documentation for an IBM .twx file, covering
  all Business Objects, services, flows, scripts, endpoints, dependencies and
  entry points. Use when the user asks to document, generate docs, create a
  technical report or export documentation for a TWX package.
allowed-tools: shell
---

## twx-docs — Generate Full Markdown Documentation

When asked to generate documentation, create a technical report or export the
full analysis of a .twx file, run:

```
python -m ibm_twx_tools docs "<path_to_file.twx>" -o "<output_path.md>"
```

Run from cwd:
`C:\Users\llopezdo\OneDrive - NTT DATA EMEAL\Documentos\NTTDATAIBMTWXSuite\NTTDATA-IBM-TWX-Suite\01_herramientas_python`

### Steps
1. Confirm the .twx file path.
2. Determine output path: if the user specified one, use it. Otherwise default to
   `<twx_filename>_docs.md` in the same folder as the .twx file.
3. Run: `python -m ibm_twx_tools docs "<twx_path>" -o "<output_path>"`
4. Confirm the file was written and report its location and size.
5. Show the user a summary of what was documented:
   - Number of Business Objects documented
   - Number of services documented
   - Number of flows diagrammed
   - Number of scripts captured
   - Number of endpoints listed

### Generated document sections
1. Application summary table
2. Business Objects / Entities
3. Services (with inputs, outputs, steps)
4. Embedded scripts (JavaScript)
5. External endpoints (REST/SOAP)
6. Process flow diagrams (Mermaid)
7. Dependency graph (Mermaid)
8. Entry points
9. Variables / Parameters
