---
name: twx-scripts
description: >
  Extracts and dumps all embedded JavaScript and server scripts from an IBM
  .twx file. Use when the user asks to see scripts, JavaScript code, server-side
  logic, Groovy scripts or embedded code inside a TWX package.
allowed-tools: shell
---

## twx-scripts — Extract Embedded Scripts

When asked to see scripts, JavaScript code, server logic or embedded code from
a .twx file, run:

```
python -m ibm_twx_tools scripts "<path_to_file.twx>"
```

Run from cwd:
`C:\Users\llopezdo\OneDrive - NTT DATA EMEAL\Documentos\NTTDATAIBMTWXSuite\NTTDATA-IBM-TWX-Suite\01_herramientas_python`

### Steps
1. Confirm the .twx file path.
2. Run: `python -m ibm_twx_tools scripts "<twx_path>"`
3. The output contains script blocks separated by lines, each with:
   - Artifact name (the service/process containing the script)
   - Step name / step ID
   - Language (typically JavaScript)
   - The script code
4. Present each script with its artifact and step context as a heading,
   then the code in a properly labeled code block.
5. If there are many scripts (>10), first show a summary table:
   | Artifact | Step | Lines |
   Then present each script on request.
6. Optionally analyze the scripts for:
   - Common patterns (REST calls, SQL queries, data transformations)
   - Potential issues or deprecated APIs
   - Migration targets for IBM BAW / CP4BA
