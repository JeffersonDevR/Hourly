---
description: Fase 7 — cuadrícula de horario con arrastrar y soltar y validación en vivo
---
Implementa `/horario` según docs/ARCHITECTURE.md ("Frontend") y `design/stitch/`.
- Cuadrícula días × bloques con vistas Curso / Docente / Aula, chips de asignatura por color, docente y aula por celda.
- Panel "Por colocar" con sesiones pendientes y cumplimiento de la malla en vivo.
- @dnd-kit: al arrastrar, pintar cada celda como válida / advertencia / bloqueada con icono + tooltip del motivo (endpoint ligero de la Fase 3). Alternativa por teclado para mover sesiones.
- Botón "Generar horario" (modo: docentes principales / habilitados; escenario de la versión — D-010; "solo esta vista"), deshacer/rehacer, indicador de ejecución del solver y estados de error/timeout.
- Semáforo y contador se actualizan tras cada cambio.
Criterios: generar el horario del Excel de demo y verlo completo y en verde; mover una sesión a una celda inválida muestra el motivo.
$ARGUMENTS
