---
description: Fase 5 — completar la API (CRUD, horarios, versiones, exportación, escenarios)
---
Completa los endpoints de docs/ARCHITECTURE.md que falten: CRUD básico de cursos/docentes/recursos/asignaciones, escenarios (crear, sin activación global — D-010), versiones de horario, publicar (bloquea si hay errores o MALLA_INCUMPLIDA), deshacer/rehacer, exportación Excel (por curso, por docente, general) y PDF.
- Esquemas Pydantic v2, errores consistentes `{codigo, mensaje}`, paginación simple.
- Incluye lo diferido de la fase 3: servicios de mutación de sesiones (colocar/mover/quitar) que validan y escriben `historial_cambio`, deshacer/rehacer, `POST /horarios/{v}/validar` (persiste: borra y regenera los conflictos de la versión, D-011) y el endpoint ligero de arrastre que devuelve el estado de cada celda (válida / advertencia / bloqueada + motivo).
- **Obligatorio:** al llamar a `validar()`, pasar siempre `horario_version.escenario_id`. El validador no puede derivar el escenario desde `EstadoHorario`, así que si se omite valida el estado base y `DOCENTE_NO_DISPONIBLE` nunca aparece con un escenario activo. Mapear el `Conflicto` del validador (codigo/gravedad/mensaje/sesion_ids) a `conflicto` + `conflicto_sesion`.
- Incluye lo diferido de la fase 4: `POST /horarios/{v}/generar` (traduce el body a `resolver(...)`, persiste las sesiones resultantes y registra `ejecucion_solver` con estado, diagnóstico y tiempos) y `POST /conflictos/{id}/propuestas` con la cadena greedy → CP-SAT con `fijas` → IA → `diagnosticar_carga` (D-003).
- Genera `docs/openapi.json` y tipos TS para el frontend (openapi-typescript) en `web/src/api/`.
Pruebas de API con TestClient para los flujos principales.
Criterios: `uv run --directory api pytest` verde; el OpenAPI describe todos los endpoints.
$ARGUMENTS
