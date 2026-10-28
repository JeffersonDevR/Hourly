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

**Decisión:** el producto se llama **Houry**. El proyecto vive en esta carpeta
(`horarios-opencode-kit/`); no se aplana a la raíz del workspace.

**Consecuencias:**
- `README.md`: la carpeta ES el proyecto, `git init` acá. Eliminada la instrucción de copiar a la raíz.
- `pyproject.toml` → `name = "houry-api"`; `package.json` → `"name": "houry-web"`.
- DB local: `sqlite:///./houry.db`.
- UI: "Houry" en `<title>`, marca de la navegación lateral y metadatos.
- Títulos de `AGENTS.md` y `README.md` con el nombre nuevo.

**No se renombra la carpeta.** El nombre del directorio es del usuario, no del producto.

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


