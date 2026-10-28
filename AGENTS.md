# Hourly — AGENTS.md

Hourly es una app web para configurar horarios escolares sin solapamientos. Hackathon: prioriza una demo end-to-end estable sobre completitud.
Flujo estrella: **importar Excel → auditar → solver → IA propone correcciones → aceptar → exportar → escenario "¿y si...?"**

## Stack (no cambiar sin preguntar)
- Backend: Python 3.12, FastAPI, SQLAlchemy 2 + Alembic, Pydantic v2, uv, pytest, ruff.
- Solver: OR-Tools CP-SAT (`api/app/solver`). Importación: `openpyxl` solo (D-016, sin pandas). Exportación: openpyxl (Excel) y reportlab (PDF).
- IA: API compatible con OpenAI (`/v1/chat/completions`) vía SDK `openai`, detrás de la interfaz `AIProvider`. Env `AI_BASE_URL`, `AI_MODEL`, `AI_API_KEY`. Implementaciones: `OpenAICompatibleProvider`, `NullProvider`, `CassetteProvider` (D-002).
- DB: SQLite en un archivo (D-001). Tipos portables para no cerrar la puerta a otro motor después: `sa.Uuid`, `sa.Enum(..., native_enum=False)`, `sa.JSON`; UUID generado en Python. `PRAGMA foreign_keys=ON` en cada conexión es obligatorio.
- Frontend: React + Vite + TypeScript, Tailwind, shadcn/ui, TanStack Query, react-router, @dnd-kit/core, zod, vitest.
- Gestores: `uv` (Python) y `pnpm` (web).

## Estructura
```
api/app/{domain,models,repositories,services,validator,solver,ai,importer,exporter,routers}
api/app/db.py (engine + PRAGMA)   api/tests   api/alembic   web/src   data/   design/stitch/   docs/
```
Fuentes de verdad: `docs/DOMAIN.md` (entidades, invariantes, mapeo del Excel) y `docs/ARCHITECTURE.md` (API, IA, solver). Léelos antes de tocar código.

## Reglas de arquitectura (innegociables)
1. **Un solo validador.** `api/app/validator` es una función pura sobre dataclasses (sin DB ni IA). La API, el solver (tests), la importación y las propuestas de IA lo reutilizan.
2. **Solver e IA desacoplados.** El solver nunca importa `app.ai`. Si la IA falla, hay timeout o no hay API key, todo funciona y la UI muestra "Asistente IA no disponible". Existe `NullProvider`. La cadena de resolución es determinista primero (D-003): reparación local greedy → CP-SAT con `fijas` → IA → `diagnosticar_carga`.
3. **No confiar en la IA.** Toda propuesta de la IA se simula sobre una copia del horario y se pasa por el validador; si deja conflictos nuevos, se descarta. Nada se aplica sin confirmación del usuario y todo cambio va a `historial_cambio` (deshacer).
4. **Invariantes duras en la DB** (índices únicos en `sesion`); las reglas blandas se registran como `conflicto`, nunca bloquean la escritura manual. Entre las blandas está `ASIGNATURA_PESADA_CONSECUTIVA`: se reporta como `advertencia` y jamás se convierte en restricción dura (D-006).
5. Los datos de la demo son `data/Datos_prueba_Gnosoft.xlsx`. Los tests golden de `docs/ARCHITECTURE.md` deben pasar siempre.

## Convenciones
- Dominio y tablas en español `snake_case` (curso, docente, sesion, bloque). Textos de UI en español neutro. Código y comentarios técnicos: español o inglés, pero consistentes.
- Python con type hints, `ruff` limpio. TypeScript `strict`. Sin `any`.
- Cada feature trae pruebas (pytest / vitest). Nada de datos inventados: usa el Excel.
- Todo estado de UI debe contemplar: vacío, cargando, error, éxito y conflicto. Nunca marcar conflictos solo con color (icono + texto). Accesibilidad AA.
- Estilo visual: moderno y amigable; usar tokens de `design/stitch/` (exportaciones de Stitch). No inventar un design system nuevo.

## Alcance
- **Fase 1 (construir):** admin único, sin login. Fase 2 (NO construir): usuarios/roles, vistas móviles, notificaciones, multi-institución. Mostrar solo "Próximamente" en la navegación.
- Las vistas para celular quedan en Fase 2 y NO se construyen en el MVP, incluida la pantalla "hoy / siguiente clase" (D-013). Ningún comando de fase ni `DEMO.md` puede pedir una ruta para celular ni esa semántica.
- Fuera de alcance del MVP: bloques dobles, grupos mixtos, sustituciones por fecha (dejar columnas/hooks, sin UI). La ausencia de un docente SÍ está en alcance, pero se modela como escenario de indisponibilidad (D-005): un "¿y si D3 no está esta semana?", no un registro histórico de sustituciones por fecha.

## Cómo trabajar
- Sigue los comandos `/fase-XX` en orden (`.opencode/commands/`). No adelantes fases.
- Antes de terminar una tarea: `uv run --directory api pytest` y `uv run --directory api ruff check .` en verde (más `corepack pnpm --dir web typecheck` si tocaste `web/`), y un resumen corto de lo hecho y lo pendiente. No hay `make` (D-015).
- Si una decisión no está en `docs/`, elige la opción más simple, anótala en `docs/DECISIONS.md` y sigue. Pregunta solo si bloquea.
