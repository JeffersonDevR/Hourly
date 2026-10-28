---
description: Fase 2 — importador de Excel con previsualización, errores por fila y confirmación
---
Implementa `app/importer` y sus endpoints según docs/ARCHITECTURE.md y el mapeo del Excel en docs/DOMAIN.md.
- Lee todas las hojas con openpyxl/pandas, ignora filas totalmente vacías, normaliza días ("Lunes"→1) y booleanos 1/0.
- **Coercionar antes de comparar.** En el archivo real `habilitado` y `disponible` llegan como `"1.0"`/`"0.0"`. Comparar contra `"1"` importa cero aptitudes y cero bloqueos sin lanzar error: es el bug más caro de esta fase. Ver "Trampas verificadas del archivo real" en `docs/DOMAIN.md`.
- Derivar lo que el Excel no trae: `bloque.tipo=clase`, `bloque.duracion_min = fin - inicio` (de seriales de Excel a minutos), y `asignatura.color` desde una paleta determinista por orden alfabético.
- Detecta y reporta con código, hoja, fila y columna: DURACION_BLOQUE_INCONSISTENTE, SIN_DESCANSOS, DUPLICADO, DOCENTE_NO_RECONOCIDO, CURSO_NO_RECONOCIDO, aptitud faltante (docente asignado sin habilitación), y DOCENTE_SOBRECARGA a nivel de asignación (D4 28/24).
- Advierte (sin bloquear) cuando `curso.estudiantes` viene en 0 o NULL y cuando `docente.max_sesiones_semana` viene en 0 o NULL: sin ese aviso, `RECURSO_CAPACIDAD` pasa vacuo o CP-SAT declara INFACTIBLE por una causa engañosa.
- `PATCH filas` permite corregir celdas y revalida. `confirmar` escribe todo en una transacción (cursos, bloques, docentes, aptitudes, recursos, asignaciones, bloqueos, escenario "Cambio") y es idempotente (D-009): upsert por clave natural (`curso.codigo`, `docente.codigo`, `bloque.codigo`, `asignatura.nombre`, `recurso.codigo`) y `asignacion_carga` por `UNIQUE(curso_id, asignatura_id)`. Reimportar el mismo archivo no duplica ni falla.
- Genera plantilla descargable `GET /api/importaciones/plantilla`.
Pruebas: golden #1 de ARCHITECTURE.md con `data/Datos_prueba_Gnosoft.xlsx`, más un Excel sucio generado en el test (duplicados, curso inexistente); e importar el mismo Excel dos veces deja exactamente los mismos conteos de filas.
Criterios: golden #1 en verde; la doble importación no duplica ni falla; la carga del estado de demo se arma en la fase 10 (D-007).
$ARGUMENTS
