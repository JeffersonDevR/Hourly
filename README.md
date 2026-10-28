# Hourly

**Los horarios escolares dejan de ser una hoja de cálculo que nadie entiende.**

Hourly importa el Excel que tu escuela ya usa, encuentra todos los solapamientos, genera el
horario completo con un solver y explica —en castellano— por qué no se puede cuando no se puede.

---

## El problema

Armar horarios a mano no falla por falta de tiempo. Falla porque nadie puede sostener en la cabeza
la simultaneidad de 4 cursos, 6 docentes, 10 asignaturas y 120 sesiones repartidas en 5 días y 6
bloques. El Excel acepta el horario imposible y no dice nada.

Hourly sí dice algo. Y dice *por qué*.

## Cómo funciona

1. **Importá el Excel.** El mismo que ya usás, con sus hojas tal como están. Sin plantilla nueva.
2. **Auditá.** Cada fila con error o advertencia, ubicada por hoja, fila y columna, corregible en línea antes de confirmar.
3. **Generá.** Un solver CP-SAT arma el horario completo respetando disponibilidad, aptitudes, topes de carga y recursos.
4. **Entendé.** Si es imposible, el diagnóstico es aritmética, no una excusa: *"D4: demanda 28 sesiones, máximo 24"*.
5. **Decidí.** Cuando hay conflicto, la IA propone correcciones. Cada propuesta se simula sobre una copia y se pasa por el validador; si introduce un conflicto nuevo, se descarta sola.
6. **Probá el "¿y si…?".** "¿D3 no está esta semana?" — la grilla se reacomoda y ves qué cambió.

## Determinista primero, IA donde aporta

Esta es la diferencia con casi todo lo demás.

- El validador, el diagnóstico y el solver son **código puro**. Sin red, sin API key, sin rate limit. Funcionan sin internet.
- La IA entra **después**, para lo que el código no puede prever: explicar un conflicto en lenguaje claro, proponer una salida, interpretar "D2 no puede dar clase los martes".
- La IA nunca se cree. Toda propuesta se valida; toda regla interpretada vuelve editable y la confirma una persona.
- Si la IA no está disponible, la app sigue completa. Solo muestra "Asistente IA no disponible".

## Estado

| Fase | Qué entrega | |
|---|---|---|
| Modelo de datos | 23 tablas, invariantes duras en la DB | ✅ |
| Importador Excel | Lectura, preview con errores por fila, upsert idempotente | ✅ |
| Validador | 11 códigos de conflicto, escenarios, gravedad por contexto | ✅ |
| Solver CP-SAT | Generación, reparación greedy, penalización blanda | 🚧 |
| API | Endpoints de sesiones, propuestas, publicación | ⬜ |
| Interfaz | Layout, grilla drag & drop, panel de conflictos | ⬜ |

Sin login, sin usuarios, sin multi-institución. Un solo administrador — es a propósito.

## Stack

| | |
|---|---|
| Backend | Python 3.12 · FastAPI · SQLAlchemy 2 · Alembic · Pydantic v2 |
| Solver | OR-Tools CP-SAT |
| IA | Cualquier API compatible con OpenAI (`AI_BASE_URL`), incluido Ollama local |
| DB | SQLite — un archivo, cero contenedores |
| Frontend | React · Vite · TypeScript · Tailwind · TanStack Query · dnd-kit |

## Correrlo

```bash
git clone https://github.com/JeffersonDevR/Hourly.git
cd Hourly
uv run --directory api alembic upgrade head
.\demo.ps1
```

Requiere `uv` y Node 24+. `pnpm` no hace falta instalarlo: el script usa `corepack`.
`.\demo.ps1 -Check` arranca, verifica `/api/estado` y baja todo sin dejar puertos colgados.

## Datos de demo

`data/Datos_prueba_Gnosoft.xlsx` no es un fixture decorativo: es el caso de prueba real.

4 cursos · 6 docentes · 10 asignaturas · 40 asignaciones · 16 recursos · **120 sesiones**.

Y trae un imposible a propósito: **D4 tiene demanda de 28 sesiones y un máximo de 24**. Con docentes
fijos el horario no existe; repartiendo Inglés entre D4 y D6, sí. Esa es la demo.

## Documentación

- [`docs/DOMAIN.md`](docs/DOMAIN.md) — entidades, invariantes y el mapeo del Excel
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — API, solver, contrato de la IA
- [`docs/DECISIONS.md`](docs/DECISIONS.md) — las 19 decisiones y por qué
- [`docs/GAPS.md`](docs/GAPS.md) — los casos que faltan, sin maquillar
- [`design/DESIGN.md`](design/DESIGN.md) — el sistema MALLA
