---
name: twx-entities
description: >
  Extracts Business Objects (BOs), data models and typed variables from an IBM
  .twx file. Use when the user asks about data structures, Business Objects,
  entities, types, parameters or the data model of a TWX package.
allowed-tools: shell
---

## twx-entities — Extract Business Objects & Data Models

When asked about entities, Business Objects, data models or variable types in
a .twx file, run:

```
python -m ibm_twx_tools entities "<path_to_file.twx>"
```

Run from cwd:
`C:\Users\llopezdo\OneDrive - NTT DATA EMEAL\Documentos\NTTDATAIBMTWXSuite\NTTDATA-IBM-TWX-Suite\01_herramientas_python`

### Steps
1. Confirm the .twx file path.
2. Run: `python -m ibm_twx_tools entities "<twx_path>"`
3. Parse the JSON array of Business Objects returned.
4. Present each BO as a table with: name, namespace, description, parent type,
   and a field table (field name, type, is_list, required, description).
5. Highlight complex types, list fields, and inheritance chains.

### Output structure
Each item in the JSON array:
```json
{
  "name": "CustomerOrder",
  "guid": "...",
  "namespace": "http://...",
  "description": "...",
  "parent": "BaseEntity",
  "fields": [
    { "name": "orderId", "type": "String", "is_list": false, "required": true, "default": null, "description": "..." }
  ]
}
```

Present all BOs. If there are more than 10, group them by namespace or by type.
