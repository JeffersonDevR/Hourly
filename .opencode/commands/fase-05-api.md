---
description: Fase 5 — completar la API (CRUD, horarios, versiones, exportación, escenarios)
---
Completa los endpoints de docs/ARCHITECTURE.md que falten: CRUD básico de cursos/docentes/recursos/asignaciones, escenarios (crear, sin activación global — D-010), versiones de horario, publicar (bloquea si hay errores o MALLA_INCUMPLIDA), deshacer/rehacer, exportación Excel (por curso, por docente, general) y PDF.
- Esquemas Pydantic v2, errores consistentes `{codigo, mensaje}`, paginación simple.
- Genera `docs/openapi.json` y tipos TS para el frontend (openapi-typescript) en `web/src/api/`.
Pruebas de API con TestClient para los flujos principales.
Criterios: `uv run --directory api pytest` verde; el OpenAPI describe todos los endpoints.
$ARGUMENTS
