---
description: Fase 3 — validador puro de conflictos y diagnóstico de carga
---
Implementa `app/validator` (puro, sin DB ni IA) con todos los códigos de la tabla de invariantes de docs/DOMAIN.md —incluido `ASIGNATURA_PESADA_CONSECUTIVA` como `advertencia` (D-006)—, más `diagnosticar_carga`.
- Entrada: dataclasses de dominio + escenario opcional (aplica `escenario_cambio` sobre la disponibilidad) + parámetro `al_publicar: bool`, que decide la gravedad devuelta de `MALLA_INCUMPLIDA`: advertencia en edición, error al publicar (D-011).
- Salida: conflictos con código, gravedad, mensaje en español simple y sesiones afectadas.
- El validador sigue siendo puro: `POST /horarios/{v}/validar` es la capa que persiste (borra los conflictos previos de esa versión y los regenera, D-011).
- Servicios para colocar/mover/quitar sesiones que validan, escriben `historial_cambio` y soportan deshacer/rehacer.
- Endpoint ligero para saber, dada una sesión en arrastre, el estado de cada celda (válida / advertencia / bloqueada + motivo).
Pruebas unitarias exhaustivas: un caso por código de conflicto (incluido `ASIGNATURA_PESADA_CONSECUTIVA`), y rendimiento (<100 ms con 120 sesiones). Excepción documentada a "nada de datos inventados": un bloque sintético `tipo=descanso` se permite SOLO en los tests de `BLOQUE_NO_CLASE` y `SIN_DESCANSOS`, porque el Excel no trae descansos.
Criterios: pruebas verdes; el validador no importa SQLAlchemy ni `app.ai`.
$ARGUMENTS
