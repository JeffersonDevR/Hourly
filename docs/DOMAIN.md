# DOMAIN.md — dominio, modelo MVP e invariantes

Modelo reducido para el MVP (el modelo completo de Fase 2 está fuera de alcance). SQLite (un archivo, D-001) con tipos portables: `sa.Uuid`, `sa.Enum(..., native_enum=False)`, `sa.JSON`, y UUID generado en Python. `PRAGMA foreign_keys=ON` obligatorio en cada conexión. PK `uuid`; `created_at`/`updated_at` en todas. Un solo horario "plantilla semanal" por versión.

## Tablas MVP
```
institucion(id, nombre, logo_url, color_acento)            -- una sola fila en Fase 1
grado(id, nombre, orden)                                    -- configurable (el Excel usa 6 y 7)
curso(id, codigo UNIQUE, nombre, grado_id FK, estudiantes)  -- '6A', '7B'
bloque(id, codigo UNIQUE, orden, inicio, fin, duracion_min, tipo ENUM[clase,descanso,almuerzo])
asignatura(id, nombre UNIQUE, color, es_pesada bool)        -- es_pesada: regla blanda D-006
docente(id, codigo UNIQUE, nombre, max_sesiones_semana, activo)   -- unidad = sesiones (bloques)
aptitud(docente_id FK, asignatura_id FK)  PK compuesta             -- quién puede dictar qué
tipo_recurso(codigo PK)                                            -- GENERAL, LAB_CIENCIAS, CANCHA, SALA_INFORMATICA (catálogo editable)
recurso(id, codigo UNIQUE, nombre, tipo_recurso FK, capacidad, curso_titular_id FK NULL)  -- 'Aula 7A' = aula titular
asignacion_carga(id, curso_id FK, asignatura_id FK, docente_principal_id FK,
                 sesiones_semana, tipo_recurso_requerido FK)       UNIQUE(curso_id, asignatura_id)
disponibilidad_bloqueo(id, docente_id FK, dia smallint(1=lunes..5), bloque_id FK,
                       origen ENUM[personal,otra_sede,otra_institucion], detalle) UNIQUE(docente_id,dia,bloque_id)
escenario(id, nombre, descripcion)
escenario_cambio(id, escenario_id FK, docente_id FK, dia, bloque_id FK, disponible_nuevo bool, motivo)
horario_version(id, numero, estado ENUM[borrador,publicado,archivado], escenario_id FK NULL, nota, publicado_at)
sesion(id, horario_version_id FK, asignacion_carga_id FK, curso_id FK, docente_id FK,
       recurso_id FK NULL, dia smallint, bloque_id FK)
  UNIQUE(horario_version_id, dia, bloque_id, docente_id)
  UNIQUE(horario_version_id, dia, bloque_id, curso_id)
  UNIQUE(horario_version_id, dia, bloque_id, recurso_id) WHERE recurso_id IS NOT NULL
conflicto(id, horario_version_id FK, codigo, gravedad ENUM[error,advertencia], estado ENUM[abierto,resuelto,ignorado], mensaje, detalle jsonb, detectado_at)
conflicto_sesion(conflicto_id FK, sesion_id FK)  PK compuesta  -- ambas FK ON DELETE CASCADE (D-011)
propuesta_resolucion(id, conflicto_id FK NULL, origen ENUM[solver,ia], titulo, explicacion, impacto, estado ENUM[pendiente,aceptada,rechazada])
propuesta_cambio(id, propuesta_id FK, tipo ENUM[mover_sesion,cambiar_docente,cambiar_recurso], sesion_id FK NULL, asignacion_carga_id FK NULL, datos jsonb)
ejecucion_solver(id, horario_version_id FK NULL, modo_docente ENUM[principal,habilitados], estado, diagnostico jsonb, iniciado_at, terminado_at)
importacion(id, archivo_nombre, estado, resumen jsonb, creada_at)
importacion_error(id, importacion_id FK, hoja, fila, columna, severidad ENUM[error,advertencia], codigo, mensaje, corregido bool)
historial_cambio(id, horario_version_id FK NULL, entidad, entidad_id, accion, antes jsonb, despues jsonb, ocurrido_at)  -- alimenta deshacer/rehacer
```
Notas: en el MVP cada sesión ocupa **un** bloque (sin bloques dobles). Vacías/sin UI (Fase 2): `usuario`, `notificacion`. Sin `institucion_id` en las demás tablas por ahora.

Notas de modelado:
- `disponibilidad_bloqueo` es el estado base del docente. Los bloques de un escenario viven SOLO en `escenario_cambio`, nunca en `disponibilidad_bloqueo`: escribirlos ahí choca con `UNIQUE(docente_id, dia, bloque_id)` cuando el docente ya tiene un bloqueo personal en esa franja (D-005).
- `horario_version.escenario_id` es la única verdad del escenario activo. `escenario` no tiene columna `activo` global (D-010).
- `docente.activo=false` lo saca del pool efectivo de `aptitud`: no recibe sesiones nuevas ni propuestas de reasignación.

## Invariantes
Duras (DB): un docente, un curso o un recurso no pueden estar en dos sesiones del mismo (versión, día, bloque).
Validador (códigos de conflicto):
| Código | Gravedad | Regla |
|---|---|---|
| DOCENTE_DOBLE / CURSO_DOBLE / RECURSO_DOBLE | error | choque en el mismo día y bloque |
| BLOQUE_NO_CLASE | error | sesión en descanso/almuerzo |
| DOCENTE_NO_DISPONIBLE | error | sesión en un bloqueo del docente (considera el escenario de la versión — D-010) |
| DOCENTE_NO_HABILITADO | error | docente sin aptitud para la asignatura |
| RECURSO_TIPO_INCORRECTO | error | el recurso no es del tipo requerido por la asignación |
| RECURSO_CAPACIDAD | error | capacidad < estudiantes del curso |
| DOCENTE_SOBRECARGA | error | sesiones del docente > max_sesiones_semana (también a nivel de asignación, antes de generar) |
| MALLA_INCUMPLIDA | advertencia o error según el parámetro `al_publicar: bool` | sesiones colocadas ≠ sesiones_semana; la gravedad se devuelve en cada evaluación, no se persisten dos verdades (D-011) |
| ASIGNATURA_PESADA_CONSECUTIVA | advertencia | dos bloques `tipo=clase` con `orden` consecutivo y sin descanso/almuerzo entre medio tienen asignaturas con `es_pesada=true`; nunca bloquea (D-006) |
Advertencias de importación: DURACION_BLOQUE_INCONSISTENTE (duración declarada vs inicio/fin), SIN_DESCANSOS, FILAS_VACIAS_IGNORADAS, DOCENTE_NO_RECONOCIDO, CURSO_NO_RECONOCIDO, DUPLICADO.

## Mapeo del Excel `data/Datos_prueba_Gnosoft.xlsx`
Las hojas traen ~1000 filas declaradas casi vacías: ignorar filas totalmente nulas.
| Hoja | Destino | Notas |
|---|---|---|
| Leeme | solo informativa | declara 50 min por bloque; `Bloques` dice 60 → advertencia, usar inicio/fin como verdad |
| Bloques | bloque | B1..B6, todos tipo `clase`; no hay descansos |
| Cursos | grado + curso | grado = dígito inicial del código (6, 7) |
| Docentes | docente | `max_sesiones_semana` |
| Asignaturas docentes | asignatura + aptitud | columna `habilitado`=1 |
| Carga | asignacion_carga | `docente_principal_id`, `sesiones_semana`, `tipo_salon_requerido` |
| Salones | tipo_recurso + recurso | "Aula 7A" → `curso_titular_id`=7A |
| Disponibilidad | disponibilidad_bloqueo | cuadrícula 1/0: guardar solo las filas con 0 (hoy: D1 Viernes B6) |
| Cambio | escenario + escenario_cambio | escenario "D2 sin clase el martes"; no altera el caso base |
Días: Lunes=1 … Viernes=5.

### Trampas verificadas del archivo real

Comprobado leyendo `data/Datos_prueba_Gnosoft.xlsx` directamente. No son suposiciones: cada una
rompe la importación en silencio si se implementa la lectura literal de la tabla de arriba.

1. **`habilitado` y `disponible` llegan como `"1.0"` / `"0.0"`, no como `"1"` / `"0"`.**
   Comparar contra `"1"` importa **cero aptitudes** y **cero bloqueos**, sin error y sin excepción.
   Coercionar a número antes de comparar (`float(v) == 1`).
2. **`inicio` y `fin` son horas, pero llegan en dos formas según la capa.** En el XML crudo son
   seriales de Excel (`0.2916667` = 07:00); `openpyxl` los devuelve como `datetime.time` (07:00)
   porque las celdas están formateadas como hora. La coerción debe aceptar AMBAS formas:
   `time`, `datetime`, serial `float` y texto. Los seis bloques van de 07:00 a 13:00.
3. **`Bloques` no trae `tipo` ni `duracion_min`.** Derivar `tipo=clase` y
   `duracion_min = fin - inicio` (60). De ahí sale `SIN_DESCANSOS`, que es correcto y esperado.
4. **`asignatura.color` no tiene fuente en el Excel.** Asignar una paleta determinista por orden
   alfabético de la asignatura, para que dos importaciones den los mismos colores.
5. **`dia` es texto español** (`Lunes`…`Viernes`). Mapear a 1..5; un valor desconocido es
   advertencia por fila, nunca excepción.
6. **`estudiantes`, `capacidad`, `sesiones_semana` y `max_sesiones_semana` son floats**
   (`"30.0"`). Convertir a `int` al persistir; comparar capacidades ya convertidas.


## Hechos verificados con CP-SAT (usar como tests golden)
- 120 sesiones: cada curso ocupa los 30 bloques (5 días × 6).
- Con `docente_principal` fijo: **imposible** — D4 demanda 28 (Inglés 16 + Ed. Física 12) y su máximo es 24.
- Con Inglés repartible entre D4 y D6 (aptitud): **factible** (ej. D4=19, D6=21 sesiones).
- Escenario D2 sin martes + Inglés repartible: **factible**; D2 conserva 25 franjas para 16 sesiones.
- D1 y D3 están exactamente en 24/24 (sin holgura). Los salones nunca son restrictivos (4 por tipo para 4 cursos).
