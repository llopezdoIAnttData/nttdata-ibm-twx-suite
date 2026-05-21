# Security Policy

## Versiones soportadas

| Versión | Soporte de seguridad |
|---------|---------------------|
| 1.1.x   | ✅ Activo            |
| 1.0.x   | ⚠️ Solo críticos     |
| < 1.0   | ❌ Sin soporte       |

## Reportar una vulnerabilidad

**No abras un issue público** para reportar vulnerabilidades de seguridad.

Envía un correo a: **security@nttdata.com** con:

1. Descripción del problema
2. Pasos para reproducirlo
3. Impacto potencial
4. Versión afectada

Recibirás confirmación en **48 horas laborales**. Haremos el fix y publicaremos un advisory en GitHub antes de divulgarlo públicamente.

## Consideraciones de seguridad de esta suite

- Los archivos `.twx` contienen lógica de negocio propietaria. **Nunca los compartas ni los subas al repositorio.** El `.gitignore` ya los excluye (`*.twx`).
- Los outputs generados (`output/`) pueden contener nombres de variables, endpoints internos y estructura de procesos. Tratar como información confidencial.
- Esta suite no hace peticiones de red. Toda la ejecución es local.

## Scope

Esta política cubre:
- El CLI Python (`01_herramientas_python/`)
- Los skills de Copilot CLI (`.copilot/skills/`)
- Los scripts de instalación (`04_scripts/`)

No cubre los archivos `.twx` que el usuario analice con la suite (son responsabilidad del usuario).
