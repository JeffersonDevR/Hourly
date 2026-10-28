---
description: Fase 9 — escenario "¿y si...?", publicación y exportación
---
Implementa en UI y API: selector de escenario (aplicar la hoja "Cambio": D2 sin clase el martes) con vista previa del impacto (sesiones afectadas, resultado del solver) antes de aplicar; Publicación (resumen de validación, publicar); exportación Excel/PDF por curso, docente y general.
- Escenario: `horario_version.escenario_id` es la única verdad del escenario activo (D-010). No hay endpoint global de activación ni columna `activo` en `escenario`. Al cambiar el escenario la grilla se re-renderiza con el resultado del solve; no hay botón "reacomodar".
- Ausencia de un docente (D-005): crear escenario → expandir sus franjas SOLO a `escenario_cambio` (nunca a `disponibilidad_bloqueo`) → `resolver(escenario, fijas=sesiones no afectadas)` → propuestas `cambiar_docente` filtradas por `aptitud` y por capacidad restante de `max_sesiones_semana` → `validar()` → confirmación del usuario.
- Versiones `publicado`: editar o borrar una sesión responde 409 y exige crear una versión borrador nueva. Implementa la regla explícitamente en los servicios de sesiones, no solo en la UI.
Criterios: aplicar el escenario re-planifica y deja 0 conflictos; los archivos exportados abren correctamente; editar o borrar una sesión de una versión publicada devuelve 409.
$ARGUMENTS
