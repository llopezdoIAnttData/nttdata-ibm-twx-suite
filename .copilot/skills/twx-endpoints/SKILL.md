---
name: twx-endpoints
description: >
  Lists all external REST, HTTP and SOAP endpoints referenced in an IBM .twx
  file. Use when the user asks about integrations, external services, APIs,
  URLs, WSDL endpoints or web service calls in a TWX package.
allowed-tools: shell
---

## twx-endpoints — List External Endpoints & Integrations

When asked about external endpoints, REST/SOAP integrations, APIs, URLs or
web service calls from a .twx file, run:

```
python -m ibm_twx_tools endpoints "<path_to_file.twx>"
```

Run from cwd:
`C:\Users\llopezdo\OneDrive - NTT DATA EMEAL\Documentos\NTTDATAIBMTWXSuite\NTTDATA-IBM-TWX-Suite\01_herramientas_python`

### Steps
1. Confirm the .twx file path.
2. Run: `python -m ibm_twx_tools endpoints "<twx_path>"`
3. Parse the JSON array of endpoints.
4. Present as a table:
   | Artifact | Integration Type | Method | URL |
5. Group by type: REST endpoints, WSDL/SOAP, HTTP generic.
6. Highlight:
   - Hardcoded URLs (potential migration issue)
   - HTTP vs HTTPS usage
   - Environment-specific patterns (localhost, dev/prod URLs)
   - External dependencies critical for migration

### Endpoint types detected
- `httpRequest` — direct HTTP calls
- `restEndpoint` — REST service definitions
- `externalService` — external service bindings
- `wsdlEndpoint` — SOAP/WSDL references
- `url` — generic URL references
