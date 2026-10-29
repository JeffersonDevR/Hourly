# DECISIONS.md — decisiones de arquitectura

Registro de decisiones tomadas fuera de `DOMAIN.md` / `ARCHITECTURE.md`, según `AGENTS.md`.
Criterio rector: **máxima estabilidad de la demo end-to-end**.

## D-001 — SQLite en lugar de PostgreSQL

**Decisión:** el MVP usa SQLite. `AGENTS.md`, `DOMAIN.md` y `fase-00`/`fase-01` deben actualizarse.

**Motivo:** el único contenedor del proyecto existía para servir a la DB. Sin Postgres desaparecen
`docker-compose.yml`, `make db-up` y el riesgo de que Docker no arranque en la máquina del pitch.
El volumen de datos (4 cursos, 6 docentes, 120 sesiones, un admin sin login) no lo justifica.

**Condiciones de portabilidad** (para que volver a Postgres sea cambiar `DATABASE_URL`):

- PK: `sa.Uuid`, no `postgresql.UUID`. UUID generado en Python (`default=uuid.uuid4`),
  nunca `server_default=text("gen_random_uuid()")`.
- Enums: `sa.Enum(..., native_enum=False)` → VARCHAR + CHECK.
- JSON: `sa.JSON`. Sin operadores `->>` en el MVP; los campos `*jsonb` se leen enteros.
- Índices únicos de `sesion`: `UNIQUE(version, dia, bloque, docente|curso|recurso)`.
  El parcial `WHERE recurso_id IS NOT NULL` es redundante (NULL ≠ NULL en ambos motores).
- Alembic con `render_as_batch=True` (SQLite no soporta `ALTER TABLE` completo).

**Obligatorio:** listener de `connect` con `PRAGMA foreign_keys=ON`. SQLite no valida FKs por
defecto y la regla 4 de `AGENTS.md` (invariantes duras en la DB) queda decorativa sin esto.
Agregar también `journal_mode=WAL` y `busy_timeout`.

**Riesgo aceptado:** el test "Postgres real (docker)" de `fase-01-db` pasa a SQLite. Si se
deploya a un PaaS con disco efímero, la DB se pierde en cada deploy.

## D-002 — Proveedor de IA estándar, no acoplado a Anthropic

**Decisión:** API compatible con OpenAI (`/v1/chat/completions`) vía SDK `openai`.

**Motivo:** el `Protocol` `AIProvider` ya desacopla la interfaz; el acoplamiento real era el SDK
en `ai/claude.py`. El estándar OpenAI-compatible cubre OpenAI, Groq, DeepSeek, Together,
OpenRouter y Ollama local sin cambiar código.

**Configuración por env:** `AI_BASE_URL`, `AI_MODEL`, `AI_API_KEY`.
Con `AI_BASE_URL=http://localhost:11434/v1` + Ollama la demo es 100% offline.

**Implementaciones:** `OpenAICompatibleProvider`, `NullProvider`, `CassetteProvider`.

**Reglas:**
- No usar `response_format={"type":"json_schema"}` (no portable). Prompt pide JSON →
  Pydantic valida → 1 reintento → `NullProvider`.
- Evitar modelos de razonamiento: emiten texto antes del JSON y rompen el parser.
- `CassetteProvider` guarda una respuesta real (una por método) y la replaya si el provider
  live falla o excede el timeout. Es el piso de la demo.

## D-003 — Cadena determinista antes que IA, para propuestas

**Decisión:** `POST /conflictos/{id}/propuestas` resuelve en este orden:

1. **Reparación local greedy** — mover sesión a franja libre válida, o cambiar docente por
   `aptitud` con capacidad, o cambiar recurso por tipo+capacidad. Determinista, <100 ms.
2. **CP-SAT con `fijas=`** — re-resuelve solo la parte rota.
3. **IA** — para lo que el código no previó.
4. **`diagnosticar_carga()`** — aritmética pura, mensaje en castellano.

**Motivo:** tres pasos deterministas antes de depender de red, key y rate limit.

**Riesgo:** el greedy es ciego en instancias sin holgura (D1 y D3 en 24/24, `DOMAIN.md`).
El paso 2 no es opcional; reacomoda cadenas de movimientos que el greedy no ve.

## D-004 — Parser determinista de reglas en lenguaje natural

**Decisión:** `interpretar_regla()` intenta primero una tabla de patrones determinista
(docente + restricción + día/bloque, ~6 formas); si no matchea, delega en la IA.

**Motivo:** el espacio de reglas del guion es chico y repetitivo. El camino crítico del pitch
no debe depender de la IA; la IA se reserva para la regla improvisada, que es donde impresiona.

**Sin cambios de comportamiento:** la regla siempre vuelve editable y el usuario la confirma.
Nunca se activa sola (`ARCHITECTURE.md`).

## D-005 — Reasignación por docente ausente vía `escenario`

**Decisión:** la ausencia de un docente se modela como escenario de indisponibilidad temporal.
No agrega tablas.

**Motivo:** `escenario` + `escenario_cambio(docente, dia, bloque, disponible_nuevo)` ya existen
en `DOMAIN.md`.

**Corrección:** los bloques de un escenario viven SOLO en `escenario_cambio`, nunca en
`disponibilidad_bloqueo`. Escribirlos en `disponibilidad_bloqueo.origen=escenario` choca con
`UNIQUE(docente_id, dia, bloque_id)` cuando el docente ya tiene un bloqueo personal en esa franja.
`disponibilidad_bloqueo` es el estado base; `escenario_cambio` es el overlay que el validador y
el solver aplican encima. Desactivar el escenario = sus filas dejan de aplicarse, sin deletes.

**No es "sustituciones por fecha":** no hay registro histórico por fecha ni calendario real.
Es un "¿y si D3 no está esta semana?" y vive en el flujo de escenarios ya construido.

**Flujo:** crear escenario → expandir sus franjas a `escenario_cambio` → `resolver(escenario,
fijas=sesiones no afectadas)` → propuestas `cambiar_docente` filtradas por `aptitud` → `validar()`
→ confirmación del usuario.

**Caso de falla esperado:** el reemplazante ya está en su `max_sesiones_semana` →
`INFACTIBLE` con diagnóstico de `diagnosticar_carga`.

**Corrección (fase 9, medida):** el flujo decía `fijas = sesiones no afectadas`. Con el Excel real
la grilla está **100% llena** (cada curso ocupa sus 30 franjas), así que dejar fijas 119 de 120
sesiones deja **una sola** franja libre para la que se mueve; si esa franja es la bloqueada, el
solver devuelve `INFACTIBLE` por construcción, no por el escenario. El escenario re-planifica la
**semana completa** con el overlay activo (`fijas=()`), que es lo que el criterio de la fase pide
("aplicar el escenario re-planifica y deja 0 conflictos"). `sesiones_afectadas` se sigue informando:
es el impacto que el usuario ve antes de confirmar.

## D-006 — Materias pesadas consecutivas: regla BLANDA

**Decisión:** `asignatura.es_pesada (bool)`. La adyacencia pesada-pesada se penaliza en el
objetivo de CP-SAT, nunca se prohíbe. El validador la reporta como advertencia
`ASIGNATURA_PESADA_CONSECUTIVA`.

**Motivo:** `DOMAIN.md:70` — cada curso ocupa los 30 bloques (5 días × 6). La grilla está 100%
llena y no hay franjas libres para usar como buffer. Prohibir todas las adyacencias pesadas
hace la instancia `INFACTIBLE` y rompe el golden test 3.

**Formulación:** por par adyacente de bloques `tipo=clase` con `orden` consecutivo y sin
descanso/almuerzo en el medio: `y >= x_b + x_{b+1} - 1`, objetivo `minimize sum(y) * penalidad`.
El Excel no trae descansos → 5 pares por día por curso.

**Corolario:** "2 horas seguidas de la misma materia" solo puede ser restricción dura si los
4 golden tests de `ARCHITECTURE.md` siguen pasando. Medir antes de promover; si alguno cae,
queda blanda.

## D-007 — Estabilidad de la demo

- **`.\demo.ps1` idempotente:** borra la DB, importa el Excel, resuelve y deja el estado exacto
  del pitch (incluye conflicto abierto + propuesta válida + ejemplo de regla NL).
  Un comando, resultado repetible.
- **`diagnosticar_carga` no se persiste.** Devuelve aritmética en memoria y se muestra en un panel.
  `conflicto.horario_version_id` es FK no nula, así que el diagnóstico de sobrecarga previo a
  generar NO puede ser una fila de `conflicto`. El conflicto abierto del demo es un
  `MALLA_INCUMPLIDA` (advertencia) sobre una versión borrador con sesiones sin colocar.
- **Solver fuera del event loop:** `run_in_threadpool`. CP-SAT con timeout de 20 s en un
  endpoint `async def` congela toda la UI, no solo el spinner.
- **Import en vivo fuera del camino crítico:** el estado del pitch viene pre-cargado.
- **`.\demo.ps1` es el único camino de arranque.** `DEMO.md` y `fase-10` deben alinearse: la
  importación en vivo se muestra como flujo aparte, nunca como primer paso del guion.

## D-008 — `generar` no destruye trabajo manual por defecto

**Decisión:** `POST /horarios/{v}/generar` trata las sesiones existentes de la versión como
`fijas`. Para regenerar desde cero hace falta `limpiar=true` explícito.

**Motivo:** sin política definida, la fase 4 y la fase 7 eligen distinto y el primer
"¿y si regenero?" borra lo que el usuario acababa de arrastrar. Destruir trabajo sin pedirlo
es el peor fallo posible en vivo.

## D-009 — Importación idempotente por `codigo`

**Decisión:** `POST /importaciones/{id}/confirmar` hace upsert por clave natural
(`curso.codigo`, `docente.codigo`, `bloque.codigo`, `asignatura.nombre`, `recurso.codigo`).
Reimportar el mismo archivo no duplica ni falla. `asignacion_carga` se resuelve por
`UNIQUE(curso_id, asignatura_id)`.

**Motivo:** con `codigo UNIQUE` y sin política, la segunda importación explota a mitad de
transacción. "La escuela manda el archivo cada trimestre" es la primera pregunta de cualquier
jurado que sepa del dominio.

## D-010 — El escenario cuelga de la versión, no es global

**Decisión:** `horario_version.escenario_id` es la única verdad del escenario activo. Se elimina
`POST /escenarios/{id}/activar` del contrato. El selector global de la UI elige el escenario de la
versión que está mostrando.

**Motivo:** `escenario` sin columna `activo`, un endpoint de activación global y
`horario_version.escenario_id` son tres verdades solapadas. Una sola: la versión sabe con qué
escenario se resolvió.

**UI:** al cambiar el escenario la grilla se re-renderiza con el resultado del solve. No hay botón
"reacomodar".

## D-011 — Ciclo de vida de `conflicto`

**Decisión:**
- `POST /horarios/{v}/validar` es autoritativo: borra los conflictos previos de esa versión y los
  regenera. Nada de acumular duplicados.
- `conflicto_sesion` con `ON DELETE CASCADE` hacia `sesion` y hacia `conflicto`.
- `MALLA_INCUMPLIDA` se evalúa con un parámetro `al_publicar: bool`; el validador devuelve la
  gravedad correspondiente en vez de persistir dos verdades.

**Motivo:** D-001 obliga a `PRAGMA foreign_keys=ON`; sin `ON DELETE` el borrado normal de una
sesión con conflicto lanza `IntegrityError`. Y el semáforo global se desincroniza dentro de la
misma demo si validar no reconcilia.

## D-012 — Fuera de alcance por inventado

**Decisión:** se cortan dos features que `fase-09` pide y ninguna fuente de verdad define:
- `enlace_consulta` (token, activar/desactivar enlaces públicos).
- Historial de versiones con comparación y "restaurar".

**Motivo:** ambas exigen migración, modelo, router y dominio que nadie especificó. No aportan al
flujo estrella y consumen tiempo de hackathon. `horario_version` conserva `numero` y `estado`;
no hay comparación ni restauración en el MVP.

## D-013 — Vista móvil fuera del MVP

**Decisión:** el MVP es solo web. `fase-09-scenario-publish` y `DEMO.md` no pueden pedir una ruta
móvil ni la semántica "hoy / siguiente clase". El pitch cierra en exportación + escenario
"¿y si...?".

**Motivo:** `AGENTS.md` ya declaraba las vistas móviles como Fase 2 y no construir, mientras
`fase-09` y `DEMO.md` las ponían como remate. Un cierre que la fuente de verdad prohíbe no se puede
mostrar en vivo. Sin esa pantalla, además, desaparece la necesidad de definir "hoy" (`bloque.inicio`
sin tipo ni timezone, sin mapeo día-semana → `dia`).

## D-014 — Nombre del producto y ubicación del proyecto

**Decisión:** el producto se llama **Hourly**. El proyecto vive en esta carpeta
(`horarios-opencode-kit/`); no se aplana a la raíz del workspace.

**Consecuencias:**
- `README.md`: la carpeta ES el proyecto, `git init` acá. Eliminada la instrucción de copiar a la raíz.
- `pyproject.toml` → `name = "hourly-api"`; `package.json` → `"name": "hourly-web"`.
- DB local: `sqlite:///./hourly.db`.
- UI: "Hourly" en `<title>`, marca de la navegación lateral y metadatos.
- Títulos de `AGENTS.md` y `README.md` con el nombre nuevo.

**No se renombra la carpeta.** El nombre del directorio es del usuario, no del producto.

**Corrección (posterior):** el nombre definitivo es **Hourly**. D-014 queda superada solo en lo
relativo al nombre; ver **D-019**.

## D-015 — Sin `make`: `demo.ps1` + comandos directos

**Decisión:** se elimina el `Makefile`. El arranque del pitch es `.\demo.ps1` (PowerShell,
incluido en Windows). Todo lo demás se invoca directo, sin alias:

| Tarea | Comando |
|---|---|
| Tests backend | `uv run --directory api pytest` |
| Lint backend | `uv run --directory api ruff check .` |
| Typecheck web | `corepack pnpm --dir web typecheck` |
| Migraciones | `uv run --directory api alembic upgrade head` |
| Demo | `.\demo.ps1` (o `-Dev` / `-Check`) |

**Motivo:** `make` no está instalado, no hay scoop ni choco, y el `Makefile` escrita por la fase 0
llamaba a `pnpm` pelado, que tampoco está (solo existe vía `corepack`). Un archivo de tareas nunca
ejecutado no es una herramienta, es deuda. `make` es además el mismo tipo de dependencia frágil que
D-001 sacó con Docker: no aporta comportamiento, solo un alias.

**Motivo técnico decisivo:** `make -j2` no puede bajar dos servidores en Windows correctamente.
Matar el wrapper de `uv` con `taskkill /T` deja al hijo de Python escuchando en el puerto, o sea
`EADDRINUSE` en el segundo arranque del pitch. `demo.ps1` envuelve cada hijo en `cmd /c` y mata el
árbol completo; verificado con `-Check`: los puertos 8000 y 5173 quedan libres al salir.

**Consecuencia:** `pnpm` no se instala. Si no está en PATH se usa `corepack pnpm` (viene con
Node 24). El script no instala nada en el sistema.

## D-016 — `openpyxl` solo, sin `pandas`

**Decisión:** el importador usa `openpyxl` únicamente. `pandas` no entra al proyecto.

**Motivo:** el dataset son 9 hojas con 40 filas útiles como máximo y ~180 en la más grande.
`pandas` agrega ~50 MB de wheels, un segundo de import en cada arranque y una capa de coerción
de tipos (NaN, floats, `NaT`) que es exactamente donde viven las trampas del archivo real
(`"1.0"` en vez de `"1"`). `openpyxl` devuelve los tipos crudos, que es lo que queremos ver.

**Consecuencia:** si el Excel creciera a decenas de miles de filas, `pandas` vuelve a tener
sentido. No es el caso de este MVP.

**Corrección (fase 4):** `ortools` declara `pandas` y `numpy` como dependencias transitivas, y
`ortools.sat.python.cp_model` importa `pandas` al cargarse. O sea: **`pandas` sí está instalado**,
aunque nuestro código no lo importe en ningún lado y el importador siga leyendo con `openpyxl`.
Dos matices honestos: el argumento del tamaño (~50 MB) **ya no aplica**, porque OR-Tools lo paga
igual; y el argumento que sí sobrevive es el de la coerción de tipos, que era el importante
(`"1.0"` en vez de `"1"`). El importador **no** pasa por `pandas`: usa `openpyxl` crudo.

## D-017 — Alcance adicional aprobado (4 features)

Features aprobadas después del alcance original. **Las cuatro caen dentro de fases existentes:
ninguna agrega una fase nueva.**

| Feature | Dónde cae | Costo real |
|---|---|---|
| **Pin de sesión** (`sesion.fijada`) | migración nueva + `fase-04` (pasa a `fijas`) + `fase-07` (toggle en la grilla) | bajo: el backend ya resuelve `fijas` (D-008) |
| **PDF / vista de impresión por docente** | `fase-09` (exporter ya planificado: openpyxl + reportlab) | casi cero si se usa `@media print` para la vista web |
| **Diff del escenario** ("se movieron N sesiones, M docentes afectados") | `fase-09`, lectura sobre `historial_cambio` / `propuesta_cambio` | bajo: los datos ya existen (`antes`/`despues`) |
| **Historial legible** ("qué cambió y cuándo") | `fase-05` (endpoint de lectura) + `fase-09` (panel) | bajo: `historial_cambio` ya existe, solo lectura |

**Pin — motivo:** es la que más valor da por línea escrita. Convierte al solver de "me borra todo"
en "trabaja conmigo", y el backend ya lo soporta por D-008. Requiere una migración nueva sobre el
esquema de la fase 1: `sesion.fijada boolean not null default false`.

**Rechazada explícitamente:** enlace público de solo lectura (`enlace_consulta`). Es el mayor valor
real para una escuela —dejar de mandar Excel por WhatsApp— pero cuesta tabla + ruta + página
pública y es la única que puede fallar delante del jurado. Queda fuera del MVP (D-012).

## D-018 — Contrato del importador y códigos de hallazgo

**Decisión:** el importador (fase 2) fija estas reglas, que ninguna otra fuente de verdad
definía. `app/importer` no importa FastAPI ni `app.ai`; la aritmética de docentes vive en
`app.validator.diagnostico`.

**1. `EstadoHorario` es la entrada compartida del validador.** `app/validator/estado.py`
define una dataclass con las colecciones del dominio (cursos, docentes, bloques, asignaturas,
aptitudes, asignaciones, bloqueos, recursos, cambios de escenario, sesiones), todas con default
vacío. `diagnosticar_carga(estado)` (fase 2) y `validar(estado, escenario)` (fase 3) consumen la
misma foto, así que un estado parcial (solo carga, sin sesiones) es válido. El importador arma
ese estado en memoria con UUID deterministas (`uuid5`), porque el diagnóstico solo compara
identificadores y en el preview todavía no existen los de la DB.

**2. `diagnosticar_carga` devuelve tres códigos**, no solo la sobrecarga. `DOMAIN.md` define la
gravedad de `DOCENTE_SOBRECARGA`, pero `ARCHITECTURE.md:5` exige además "vs. franjas
disponibles" y "asignaturas con un único docente habilitado":

| Código | Gravedad | Regla |
|---|---|---|
| `DOCENTE_SOBRECARGA` | error | demanda del docente principal > `max_sesiones_semana` |
| `DOCENTE_SIN_HOLGURA` | error | demanda > franjas de clase libres (5 días × bloques `clase` − bloqueos − cambios de escenario) |
| `ASIGNATURA_UNICO_DOCENTE` | advertencia | asignatura con demanda y 0 o 1 aptitudes: sin margen para reasignar |

Los tres son diagnóstico en memoria y no se persisten (D-007). Con el archivo real:
1 `DOCENTE_SOBRECARGA` (D4, 28 > 24) y 9 `ASIGNATURA_UNICO_DOCENTE` (todas menos Inglés).

**Corrección (fase 12) — tipo de bloque inferido:** la hoja `Bloques` no tiene columna `tipo`, y
antes toda fila se importaba como `clase`. Un colegio cuyo Excel trae un recreo lo veía convertirse
en bloque de clase y el solver podía meter una sesión ahí. Ahora `duracion_min <= 30` ⇒ `descanso`
(las clases reales duran 45–60), y el análisis reporta `RECREO_INFERIDO` (no bloqueante) listando
los bloques que infirió. Con el archivo real no cambia nada: sus 6 bloques duran 60.

**3. Códigos de hallazgo del importador.** Además de los de `DOMAIN.md` (`DURACION_BLOQUE_INCONSISTENTE`,
`SIN_DESCANSOS`, `FILAS_VACIAS_IGNORADAS`, `DUPLICADO`, `DOCENTE_NO_RECONOCIDO`,
`CURSO_NO_RECONOCIDO`), el importador reporta `APTITUD_FALTANTE` (docente asignado sin
habilitación), `ASIGNATURA_NO_RECONOCIDA`, `TIPO_RECURSO_NO_RECONOCIDO`, `BLOQUE_NO_RECONOCIDO`,
`DIA_NO_RECONOCIDO`, `HOJA_FALTANTE`, `VALOR_REQUERIDO`, `BLOQUE_INVALIDO`,
`CURSO_SIN_ESTUDIANTES` y `DOCENTE_SIN_MAXIMO`. Todos llevan hoja, fila y columna.
`ASIGNATURA_UNICO_DOCENTE` es un diagnóstico, no un hallazgo de celda: no tiene fila.

**4. Bloqueantes vs. no bloqueantes.** `severidad` describe el dato; `bloqueante` decide si la
fila se puede escribir. Son ejes distintos:

- No bloqueantes: `DURACION_BLOQUE_INCONSISTENTE`, `SIN_DESCANSOS`, `FILAS_VACIAS_IGNORADAS`,
  `DOCENTE_SOBRECARGA`, `CURSO_SIN_ESTUDIANTES`, `DOCENTE_SIN_MAXIMO`, `DIA_NO_RECONOCIDO`.
  El archivo real se confirma entero aunque D4 esté sobrecargado: la sobrecarga es un problema
  del solver, no de la escritura.
- El resto bloquea su fila: la confirmación la omite y escribe las demás.

`DIA_NO_RECONOCIDO` es advertencia por pedido explícito de la fase 2 ("nunca una excepción"),
pero la fila se omite igual porque `disponibilidad_bloqueo.dia` es NOT NULL.

**5. `estudiantes` y `max_sesiones_semana` en 0 o vacío** se avisan (`CURSO_SIN_ESTUDIANTES`,
`DOCENTE_SIN_MAXIMO`) y se guardan como 0. Esos dos ceros son el tope duro que CP-SAT tomaría al
pie de la letra; el aviso nombra la causa real antes de que el solver diga INFACTIBLE.

**6. Cada reanálisis es autoritativo.** `POST /importaciones` y `PATCH .../filas` borran y
regeneran los `importacion_error` de esa importación, igual que `POST /horarios/{v}/validar`
(D-011). `importacion_error.corregido` no se usa en la fase 2: la fila corregida desaparece del
set, así que no quedan errores fantasma.

**7. `disponibilidad_bloqueo` importado usa `origen=personal`** y
`detalle="Importado de la hoja Disponibilidad"`: el Excel no distingue el motivo y el enum de
`DOMAIN.md` no tiene un valor "importado" (agregarlo sería un valor de enum inventado).

**8. `PATCH .../filas` identifica la celda por `(hoja, fila, columna)`**, con la fila de Excel y
el encabezado (o la letra) de la columna, los mismos valores que devuelve el hallazgo. El libro se
reanaliza completo: no hay una segunda ruta de validación.

**9. `importacion.resumen` guarda las hojas crudas JSON-safe** (`time` → `"HH:MM:SS"`), no las
entidades ya convertidas. Así el preview, el PATCH y la confirmación parten del mismo registro y
una corrección no necesita volver a subir el archivo.

**10. Corrección a `DOMAIN.md`, trampa 2.** `openpyxl` devuelve `datetime.time` para `inicio` y
`fin` del archivo real: las celdas están formateadas como hora, así que la conversión de serial
no ocurre. El serial (`0.2916667 * 24 * 60 = 420`) sigue soportado porque un Excel generado por
otra herramienta sí lo trae. Ambas rutas se prueban en `tests/test_importer_coercion.py`.

## D-019 — El producto se llama **Hourly** (reemplaza D-014 en lo relativo al nombre)

**Decisión:** el nombre del producto es **Hourly**, no "Houry". D-014 queda superada solo en lo
que respecta al nombre; el resto de D-014 —que el proyecto vive en `horarios-opencode-kit/` y que
no se aplana a la raíz— sigue vigente.

**Motivo:** decisión explícita del usuario. "Hourly" se lee como "cada hora" y resulta más
pegadizo que "Houry".

**Consecuencias (ya aplicadas):**
- `pyproject.toml` → `name = "hourly-api"`; `package.json` → `"name": "hourly-web"`.
- DB local: `sqlite:///./hourly.db`.
- UI: "Hourly" en `<title>`, marca de la navegación lateral y metadatos.
- Marca gráfica: H geométrica con travesaño lila `#C4B5FD` y punto crema `#F2E6A9`. El SVG, las
  clases y la escala están en `design/stitch/tokens.css`, sección MARCA.
- El turquesa `#5EEAD4` no se usa en la marca: está reservado a las propuestas de la IA.

**Nota de mantenimiento:** esta decisión se numeró `D-018` por error, duplicando el número de
"Contrato del importador". Queda renumerada como `D-019`; la siguiente decisión nueva es `D-020`.

## D-020 — Solve en dos fases con presupuesto determinista

**Decisión:** `resolver()` corre dos fases. Fase 1 busca un plan válido sin objetivo (0.3–0.6 s).
Fase 2 mejora con un presupuesto **determinista** (`max_deterministic_time=0.5`) además del
`SOLVER_TIMEOUT_S` de reloj, que sigue siendo el tope duro.

**Motivo (medido, no estimado):** el óptimo exacto de "cero huecos" es una aguja: CP-SAT lo
encuentra a los **~13 s de reloj** (4.6 unidades deterministas). Con el tope de 20 s no se cumple
el criterio de "<10 s" de la fase, y cortar por reloj haría que el plan dependa de la velocidad de
la máquina del pitch. Con presupuesto determinista: `0.5` → 7 huecos en ~2.5 s, `1.0` → 6 huecos,
sin presupuesto → 0 huecos en 13 s.

**Consecuencia:** la generación completa devuelve **`FACTIBLE`, no `OPTIMO`**. Es deliberado: un
plan en 2.5 s que el jurado ve nacer vale más que un óptimo que llega cuando ya cambiaste de tema.
Generación en frío end-to-end: **4.86 s**.

**Desviaciones asociadas al contrato de `ARCHITECTURE.md`:**
- Código nuevo **`RECURSO_NO_DISPONIBLE`**: el validador no tenía código para "no hay aula libre del
  tipo y capacidad" (sus `RECURSO_*` describen un recurso asignado pero inválido).
- `Resultado.objetivo: int | None`, campo extra sobre `(estado, sesiones, diagnostico)`, para poder
  medir el efecto de la penalización de materias pesadas.
- La restricción "exactamente una sesión por curso y franja" pasa a `<= 1` cuando la malla no llena
  la semana; literalmente `== 1` volvería `INFACTIBLE` cualquier estado parcial.
- El greedy desempata por datos del dominio (día, bloque, curso, asignatura) y no por `sesion.id`:
  con `uuid4` el desempate por id dejaría de ser determinista.


## D-021 — Contrato de la API de horarios (fase 5)

Decisiones que la fase 5 tuvo que tomar porque ninguna fuente de verdad las definía.

**1. Errores de la API: `{codigo, mensaje}` en el nivel superior.** Un handler de
`HTTPException` en `main.py` aplana el `detail`. `importaciones` cambió de `{detail}` a este
formato y ningún consumidor dependía del anterior. Códigos de la fase: `NO_ENCONTRADO`,
`REFERENCIA_INVALIDA`, `CODIGO_DUPLICADO`, `NOMBRE_DUPLICADO`, `EN_USO`, `ASIGNACION_DUPLICADA`,
`VERSION_PUBLICADA`, `BLOQUE_NO_CLASE`, `DOCENTE_DOBLE`, `CURSO_DOBLE`, `RECURSO_DOBLE`,
`CONFLICTOS_ABIERTOS`, `SESION_DUPLICADA`, `NADA_QUE_DESHACER`, `NADA_QUE_REHACER`,
`PROPUESTA_CERRADA`, `PROPUESTA_INVALIDA`, `FORMATO_NO_SOPORTADO`.

**2. Una versión `publicado` es inmutable: editar, mover o borrar una sesión responde 409
`VERSION_PUBLICADA`.** Está en el servicio, no en la UI, y adelanta el criterio que `fase-09`
pide explícitamente. Deshacer y rehacer también exigen borrador: si no, se podría editar
indirectamente una versión publicada.

**3. Deshacer/rehacer necesita una columna: `historial_cambio.deshecho` (migración
`9c1f0a7d2b3e`).** Deshacer marca la entrada en vez de borrarla y rehacer la reaplica. Cualquier
mutación nueva borra las entradas deshechas, así que **el redo no sobrevive a otra edición**
(el caso que `GAPS.md` dejaba abierto).

**4. `generar` persiste por diferencia, no truncando.** `resolver` devuelve fijas + generadas con
el id original de las fijas (`id_sesion` es `uuid5`), así que sólo se insertan las nuevas, se
actualizan las movidas y se borran las que sobran. Reinsertar todo cambiaría los ids de lo que
no se movió y rompería las referencias del historial.

**5. `POST /horarios/{v}/sesiones` no corre `validar()` antes de escribir.** Las invariantes
duras las impone la DB (D-001) y el `IntegrityError` se traduce al código del conflicto
(`DOCENTE_DOBLE`/`CURSO_DOBLE`/`RECURSO_DOBLE`) dentro de un `SAVEPOINT`. Las reglas blandas
nunca bloquean la escritura (regla 4 de `AGENTS.md`); se ven al validar.

**6. Exportación: Excel en la fase 5, PDF en la fase 9.** `reportlab` no está instalado y
D-017 ya asigna el PDF de docente a la fase 9; `formato=pdf` responde 400
`FORMATO_NO_SOPORTADO`. Vistas: `curso`, `docente`, `recurso` y `general` (una hoja por curso).

**7. Propuestas: greedy ahora, CP-SAT con `fijas` e IA en las fases 8 y 9.** `POST
/conflictos/{id}/propuestas` corre `reparar_greedy` y, si no hay propuestas válidas, devuelve
`alerta` con `diagnosticar_carga`. El paso 2 de D-003 (CP-SAT con `fijas`) llega con el flujo
de escenarios de la fase 9 y el paso 3 (IA) con la fase 8.

**8. `GET /horarios/{v}/arrastre` valida 30 veces por request** (una por franja de clase),
~50 ms. Es aceptable para una grilla de demo; si la UI lo llama en cada movimiento, hay que
cachear las reglas que no dependen de la sesión.

## D-022 — Reglas en lenguaje natural: dónde aterrizan y qué no hace la IA

Cierra el hueco que `fase-08` dejaba abierto: `POST /reglas/interpretar` devolvía una regla
"editable" sin decir dónde se guardaba.

**1. No hay tabla `regla`.** Una restricción "tal docente no puede tal día/bloque" es exactamente
`disponibilidad_bloqueo(docente_id, dia, bloque_id, origen, detalle)`. Confirmar una regla = escribir
esas filas con `origen=personal` y `detalle="Regla: <texto>"`. Borrar una regla = borrar esas filas.
El validador y el solver ya la respetan sin tocar nada.

**2. `POST /reglas/confirmar` es el único que escribe.** Idempotente por
`UNIQUE(docente_id, dia, bloque_id)`: confirmar dos veces no duplica. `bloquea=false` libera (borra)
en vez de bloquear, para que "D3 libre el viernes B6" signifique algo.

**3. La interpretación tiene tres orígenes, en este orden:** parser determinista (D-004, sin red),
proveedor de IA, y modo manual (tarjeta vacía con el mensaje). Si no hay proveedor y el parser no
matchea, **no se inventa una regla**: se abre la tarjeta para elegir a mano.

**4. `generar` persiste el diagnóstico cuando falla.** D-007 dice que `diagnosticar_carga` no se
persiste *antes* de generar (no hay versión). Cuando la generación devuelve `INFACTIBLE`/`TIMEOUT`
**sí** hay versión, y el motivo se escribe como `conflicto` de esa versión para que aparezca donde el
usuario resuelve todo. Con el Excel real: `DOCENTE_SOBRECARGA` de D4 (28 > 24) más
`ASIGNATURA_UNICO_DOCENTE` ×9 (advertencias) y `MALLA_INCUMPLIDA` ×40.

**5. La IA nunca escribe el horario.** Sus propuestas se aplican sobre una copia, se pasan por
`validar()` y se descartan si agregan conflictos duros que antes no estaban (comparación de conjuntos
`(codigo, sesion_ids)`, no de conteos). Usa **códigos** (`D6`, `B3`), nunca ids: un id inventado por
el modelo no puede llegar a la DB porque no resuelve.

**6. Corrección del guion de demo.** `DEMO.md` paso 3 pedía "pasar parte de Inglés a D6 → aceptar →
verde". No cierra: D4 sobran **4** sesiones y D6 tiene **3** de margen (21/24). Lo que resuelve la
versión es generar con docentes habilitados (D4≈19, D6≈21). La IA se muestra en un conflicto de
sesión, donde sí tiene margen. `DEMO.md` y `design/stitch/README.md` §4 quedaron corregidos.

## D-023 — Pin de sesión y entrada manual de datos

Cierra D-017 (el pin) y el hueco que impedía cargar un colegio sin Excel.

**1. `sesion.fijada` y la regla del pin.** Migración `b7c2e1f4a9d3`:
`sesion.fijada boolean not null default false`.

`generar` calcula `fijas = [sesiones con fijada] o None`:

| Situación | Qué hace el solver | Por qué |
|---|---|---|
| **Ninguna** sesión fijada | Trata las existentes como fijas (D-008) | Regenerar no puede destruir trabajo manual sin que nadie lo pida |
| **Al menos una** fijada | Mueve todo lo que no está fijada | El usuario declaró qué le importa; eso convierte el solver en "trabaja conmigo" |

Es la única forma de que el pin signifique algo sin romper D-008: sin pins nada cambia, y pinear es
un acto explícito. El escenario "¿y si…?" usa la misma regla.

**2. Trampa encontrada por test:** `asignar_recursos` reconstruía cada `Sesion` para ponerle el aula
y **descartaba `fijada`**. La sesión quedaba en la franja correcta pero perdía el pin. Cualquier
reconstrucción de `Sesion` tiene que copiar el campo.

**3. Entrada manual completa.** La API tenía CRUD de cursos, docentes, recursos y asignaciones, pero
`bloques`, `asignaturas` y `grados` eran **solo lectura**. Consecuencia: un colegio sin Excel no podía
crear un curso (falta el grado) ni cargar sus **recreos** (falta el bloque). Se agregaron
`POST/PATCH/DELETE` para los tres.

`bloque.duracion_min` se **deriva** de `inicio`/`fin`; si el cliente la manda y no coincide responde
400 `DURACION_INCONSISTENTE`. El Excel real ya trae esa inconsistencia como advertencia
(`DURACION_BLOQUE_INCONSISTENTE`); por API se rechaza antes de escribir.

**4. Los descansos se ven.** La grilla filtraba solo bloques `clase`, así que un recreo existía en la
base pero no en pantalla. Ahora los bloques `descanso` y `almuerzo` se dibujan como filas
informativas (sin celdas arrastrables): "Recreo · 09:00–09:20 · sin sesiones". El solver y el
validador ya los respetaban (`bloques_clase`, `BLOQUE_NO_CLASE`); faltaba mostrarlos.

**5. Pantalla de configuración.** La entrada manual no existía en la UI: `Cursos`, `Docentes` y
`Recursos` eran listas de solo lectura. Se agregó `/configuracion` con formulario y tabla para las
nueve piezas (grados, bloques, asignaturas, tipos de recurso, cursos, docentes, recursos, carga
académica y aptitudes). Faltaban además dos endpoints sin los cuales nada de eso cerraba:
`tipos-recurso` (un recurso necesita un tipo) y `aptitudes` (sin ellas el solver no puede repartir
una asignatura entre dos docentes).

Verificado de punta a punta con una base **vacía**: cargar grado → bloques (uno de clase y un
recreo) → asignatura → tipo → curso → docente → recurso → asignación → aptitud → generar.
Resultado: 4 sesiones, 0 errores y **0 sesiones en el recreo**.
