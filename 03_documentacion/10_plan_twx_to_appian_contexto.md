# CONTEXTO DE SESIÓN — Plan IBM BPM → Appian Automatizado
**Archivo para continuar la conversación en una sesión futura**
**Última actualización: 21 Mayo 2026**

---

## ¿Dónde quedamos?

Estamos planeando construir el **puente automático IBM BPM → Appian** usando:
- La suite `ibm_twx_tools` ya construida (extracción del .twx → JSON)
- Un nuevo módulo `appian_generator` (JSON → .zip Appian importable)
- Un nuevo skill `/twx-to-appian` en Copilot CLI

**La Fase 1 está lista para arrancar.** Solo falta que el usuario traiga el `.zip` de exportación de Appian.

---

## Frase para retomar la sesión

```
Continuemos el plan twx-to-appian.
Tengo el .zip de exportación de Appian listo para que lo analices.
El plan está en 03_documentacion/10_plan_twx_to_appian.html
```

---

## Lo que ya tenemos ✅

| Recurso | Ubicación |
|---------|-----------|
| Suite Python ibm_twx_tools | `OneDrive/.../01_herramientas_python/` |
| JSON de 10 procesos Profuturo | Sesión anterior (extracción completa) |
| 16 Skills Copilot CLI | `~/.copilot/skills/` + GitHub repo |
| Repo GitHub | `llopezdoIAnttData/nttdata-ibm-twx-suite` |
| Acceso a consola Appian | Usuario confirmó acceso |

## Lo que necesitamos para Fase 1 ⏳

1. **`.zip` de exportación de Appian** → para hacer ingeniería inversa del schema XML
2. **Versión de Appian** del entorno Profuturo (ver en consola: Admin → About)
3. **URL de documentación Appian** que el usuario mencionó tener
4. **Appian Import API** → investigar si está disponible en la consola (opcional)

---

## Arquitectura del nuevo módulo

```
appian_generator/
├── record_type_builder.py      ← BOs (12.*) → Record Types XML
├── constant_builder.py         ← Variables (62.*) → Constants XML
├── integration_builder.py      ← Endpoints → Integration Objects XML
├── expression_rule_builder.py  ← Scripts JS → Appian Expression Language (LLM)
├── process_model_builder.py    ← BPDs (25.*) → Process Models XML (LLM)
├── interface_builder.py        ← Coach Views (64.*) → SAIL Interfaces (LLM)
└── package_assembler.py        ← Todo → .zip Appian importable
```

## Nuevo skill a crear

```
/twx-to-appian
→ Pregunta: ¿Ruta del .twx?
→ Extrae con ibm_twx_tools (ya existe)
→ Genera .zip Appian con appian_generator
→ Resultado: MiProceso_AppianPackage.zip
```

---

## Complejidad por tipo de artefacto

| IBM | Appian | Complejidad |
|-----|--------|-------------|
| Business Object (12.*) | Record Type | 🟢 Baja — mapeo directo |
| Variable de entorno (62.*) | Constant | 🟢 Baja — mapeo directo |
| Endpoint REST/SOAP | Integration Object | 🟡 Media |
| Servicio IS SYNC | Expression Rule | 🟡 Media |
| Script JavaScript | Expression Rule | 🔴 Alta — LLM traduce JS → Appian EL |
| BPD completo (25.*) | Process Model | 🔴 Alta — LLM reimagina el flujo |
| Coach View / HHS (64.*) | Interface SAIL | 🔴 Alta — LLM genera SAIL |

---

## Plan de 5 fases

1. **F1** — Ingeniería inversa del .zip Appian (1 sesión)
2. **F2** — Tablas de mapeo IBM → Appian (1-2 sesiones)
3. **F3** — Construcción appian_generator (3-5 sesiones, 5 sprints)
4. **F4** — Skill /twx-to-appian en Copilot CLI (1 sesión)
5. **F5** — Validación con Redención de Bono en consola real (1-2 sesiones)

---

## Archivos relacionados

```
03_documentacion/
├── 10_plan_twx_to_appian.html           ← El HTML con el plan completo
├── 10_plan_twx_to_appian_contexto.md    ← Este archivo
├── 09_status_report_22mayo.html         ← Status report de todo lo hecho
├── 08_onboarding_equipo.html            ← Onboarding Carlos y Pavel
└── 05_roadmap_automatizacion_appian.html ← Roadmap previo (referencia)
```

---

*NTT DATA EMEAL · IBM TWX Suite v1.1.0 · Proyecto Profuturo IBM BPM → Appian*
