# ARCHITECTURE.md — API, solver, IA, pruebas

## Módulos backend (`api/app`)
- `domain/`: dataclasses inmutables (Curso, Docente, Bloque, Asignacion, Sesion, Recurso, Bloqueo…). Sin SQLAlchemy.
- `validator/`: `validar(estado, escenario=None) -> list[Conflicto]`. Puro, rápido (<100 ms para 120 sesiones). También `diagnosticar_carga(estado) -> list[Diagnostico]` (aritmética: demanda por docente vs. máximo y vs. franjas disponibles; asignaturas con un único docente habilitado).
- `solver/`: `resolver(estado, modo_docente, escenario, fijas=[]) -> Resultado(estado: OPTIMO|FACTIBLE|INFACTIBLE|TIMEOUT, sesiones, diagnostico)`.
  - CP-SAT, variable booleana por (asignación, docente permitido, día, bloque). Restricciones: cada curso exactamente 1 sesión por (día,bloque) de clase; suma por asignación = sesiones_semana; docente ≤ 1 por franja; docente ≤ max_sesiones; sin sesiones en bloqueos del docente (aplicando el escenario).
  - `modo_docente=principal` usa solo `docente_principal`; `habilitados` usa `aptitud`.
  - Objetivo blando de materias pesadas (D-006): por cada par adyacente de bloques `tipo=clase` con `orden` consecutivo y sin descanso/almuerzo en el medio, `y >= x_b + x_{b+1} - 1` y `minimize sum(y) * penalidad`. Nunca es restricción dura.
  - Asignación de recursos en un paso posterior (emparejamiento por franja: tipo + capacidad; preferir aula titular). Si en una franja no hay recurso libre del tipo requerido, se reporta como caso diagnosticable (`RECURSO_*` con causa), nunca queda en silencio. `fijas` permite regenerar solo una parte (sesiones ya colocadas que no se tocan).
  - Si es INFACTIBLE, devolver `diagnostico` determinista (p. ej. "D4: demanda 28 > máximo 24") usando `diagnosticar_carga`. Timeout por defecto 20 s.
- `ai/`: `AIProvider` (Protocol) con `explicar_y_proponer(conflicto, contexto) -> list[PropuestaIA]`, `interpretar_regla(texto) -> ReglaEstructurada`, `disponible() -> bool`. Implementaciones: `OpenAICompatibleProvider` (SDK `openai` contra `/v1/chat/completions`, salida JSON validada con Pydantic, timeout 20 s, 1 reintento), `NullProvider` y `CassetteProvider` (una respuesta real por método, replayada si el live falla o expira). Config por env `AI_BASE_URL`/`AI_MODEL`/`AI_API_KEY`. Todo error → `NullProvider` + `ai_disponible=false`.
- `importer/`: lee Excel multi-hoja → `PreviewImportacion` con errores/advertencias por fila; endpoint de confirmación escribe en DB en una transacción. Soporta corrección en línea antes de confirmar.
- `exporter/`: Excel (por curso, por docente, general) y PDF.
- `routers/`: FastAPI, prefijo `/api`.

## Orden de resolución de un conflicto (D-003)
Determinista primero: reparación local greedy (mover sesión a franja libre válida / cambiar docente por `aptitud` con capacidad / cambiar recurso por tipo+capacidad) → CP-SAT con `fijas` → IA → `diagnosticar_carga`. El paso de CP-SAT no es opcional: reacomoda cadenas de movimientos que el greedy no ve.

## Contrato de la IA
Entrada: conflicto + sesiones afectadas + docentes/aptitudes/disponibilidad relevantes (JSON compacto, nunca el horario completo). Salida obligatoria (JSON): `{"propuestas":[{"titulo","explicacion_simple","impacto","cambios":[{"tipo":"mover_sesion|cambiar_docente|cambiar_recurso", ...}]}]}` con 2 a 3 propuestas. Tono: claro, breve, sugerente.
Pipeline: IA → parsear → **simular cambios sobre copia → `validar()`** → descartar propuestas que introduzcan conflictos → guardar como `propuesta_resolucion` (origen `ia`) → mostrar antes/después. Si quedan 0 propuestas válidas o la IA no está disponible: devolver alerta con la causa probable de `diagnosticar_carga` ("faltan N sesiones de capacidad del docente X").
Lenguaje natural → regla: la IA devuelve una regla estructurada editable; el usuario la revisa antes de guardar (nunca se activa sola).

## Endpoints (`/api`)
```
GET  /estado                      → conteos, semáforo, ai_disponible
POST /importaciones               → sube xlsx, devuelve preview + errores
PATCH /importaciones/{id}/filas   → corrige celdas
POST /importaciones/{id}/confirmar
GET  /cursos /docentes /recursos /bloques /asignaciones  (+ CRUD básico)
GET/POST /escenarios
POST /horarios                    → crea versión borrador
GET  /horarios/{v}/vista?por=curso|docente|recurso&id=
POST /horarios/{v}/sesiones       → colocar; PATCH mover; DELETE quitar (valida y registra historial)
POST /horarios/{v}/validar        → conflictos
POST /horarios/{v}/generar        → {modo_docente, escenario_id?, solo_curso_id?, limpiar?} → ejecucion_solver
                                    (las sesiones existentes de la versión se tratan como `fijas`; `limpiar=true` las borra, D-008)
GET  /horarios/{v}/conflictos
POST /conflictos/{id}/propuestas  → solver primero; si falla, IA; si falla, alerta con diagnóstico
POST /propuestas/{id}/aceptar | /rechazar
POST /horarios/{v}/deshacer | /rehacer
POST /horarios/{v}/publicar ; GET /horarios/{v}/exportar?formato=xlsx|pdf&por=...
POST /reglas/interpretar          → lenguaje natural → regla (IA)
```

## Pruebas golden (deben pasar siempre)
1. Importar el Excel → 4 cursos, 6 docentes, 10 asignaturas, 40 asignaciones, 16 recursos, 1 bloqueo; advertencia DURACION_BLOQUE_INCONSISTENTE; diagnóstico DOCENTE_SOBRECARGA (D4 28/24) a nivel de asignación.
2. `resolver(modo=principal)` → INFACTIBLE con diagnóstico que menciona D4.
3. `resolver(modo=habilitados)` → solución con 120 sesiones y `validar()` sin errores; ningún docente > 24.
4. Con escenario "D2 sin martes": factible, D2 sin sesiones el martes, 0 conflictos.
5. Con `NullProvider`, los flujos 1–4 funcionan y `/estado.ai_disponible=false`.
6. Una propuesta de IA que cause un choque es descartada (test con proveedor simulado).
7. Índices únicos de `sesion` rechazan duplicados.
8. Con dos asignaturas `es_pesada=true` en bloques consecutivos del mismo curso, `validar()` reporta `ASIGNATURA_PESADA_CONSECUTIVA` con gravedad `advertencia` y no la convierte en error; sin adyacencia pesada el código no aparece.

## Frontend
Rutas: `/` Inicio, `/importar`, `/cursos`, `/docentes`, `/recursos`, `/reglas`, `/horario`, `/conflictos`, `/publicacion`. Barra global: año/institución, guardado, semáforo (icono+texto), contador de conflictos, selector de escenario. `/horario`: cuadrícula días × bloques, vistas curso/docente/aula, panel "Por colocar", arrastrar con @dnd-kit marcando celdas válidas / advertencia / bloqueadas con tooltip del motivo (llama a un endpoint ligero de validación o valida en cliente con las mismas reglas expuestas por la API). Navegación por teclado.
