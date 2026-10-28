# STATE.md — punto de entrada para retomar

> **Leé este archivo primero** si abrís el repo en otra máquina, otra sesión o después de un corte.
> Es el estado operativo. El producto está en `README.md`; las reglas en `AGENTS.md`.

## Dónde estamos

**Fases 0 a 4 cerradas. La siguiente es la 5.**

| Fase | Comando | Entrega | Estado |
|---|---|---|---|
| 0 | `/fase-00-scaffold` | Monorepo, `demo.ps1`, layout | ✅ |
| 1 | `/fase-01-db` | 23 tablas, migración, repositorios | ✅ |
| 2 | `/fase-02-import` | Importador Excel, preview, upsert | ✅ |
| 3 | `/fase-03-validator` | `validar()` puro, 11 códigos | ✅ |
| 4 | `/fase-04-solver` | CP-SAT, greedy, escenario | ✅ |
| 5 | `/fase-05-api` | CRUD, sesiones, `generar`, arrastre | ⬜ **siguiente** |
| 6 | `/fase-06-ui-shell` | Layout y pantallas | ⬜ |
| 7 | `/fase-07-ui-grid` | Grilla drag & drop | ⬜ |
| 8 | `/fase-08-conflicts-ai` | IA, propuestas, reglas NL | ⬜ |
| 9 | `/fase-09-scenario-publish` | Escenarios, publicación, export | ⬜ |
| 10 | `/fase-10-demo` | Estado precargado del pitch | ⬜ |

Los prompts de cada fase están en `.opencode/commands/`. **No adelantes fases**: cada una asume la
anterior.

## Qué instalar (y qué NO)

| Sí | Por qué |
|---|---|
| `git` | obvio |
| `uv` | baja Python 3.12 solo, según `api/.python-version` |
| Node 24+ | trae `corepack`, que provee pnpm |

**NO instalar:** `make` (D-015, se eliminó), `pnpm` (basta corepack), **Docker** (no hay contenedores),
ningún motor de base de datos (SQLite es un archivo).

## Puesta en marcha en una máquina nueva

```bash
git clone https://github.com/JeffersonDevR/Hourly.git
cd Hourly
uv run --directory api alembic upgrade head
.\demo.ps1 -Check
```

Salida esperada: `API OK ok=True ai_disponible=False`, y después `puerto 8000 libre` /
`puerto 5173 libre`. Si los puertos quedan ocupados, algo quedó colgado.

Tests: `uv run --directory api pytest` → **182 passed**.
Lint: `uv run --directory api ruff check .` → limpio.

## Cómo retomar el trabajo

1. `AGENTS.md` — reglas innegociables y stack.
2. `docs/STATE.md` — este archivo.
3. `docs/DECISIONS.md` — **20 decisiones**. Si algo contradice un doc viejo, gana la decisión.
4. Correr `.\demo.ps1 -Check` y `pytest`. Si eso no está verde, no sigas.
5. Lanzar `/fase-05-api` en OpenCode.

## Trampas ya pagadas — no las vuelvas a descubrir

- **El Excel trae `"1.0"`, no `"1"`.** Comparar contra `"1"` importa cero aptitudes y cero bloqueos
  sin lanzar error. Ver `docs/DOMAIN.md`, sección "Trampas verificadas del archivo real".
- **`openpyxl` devuelve `datetime.time`**, no seriales de Excel, para `inicio`/`fin`.
- **`validar()` necesita `escenario_id` explícito.** Si la fase 5 lo omite, valida el estado base y
  `DOCENTE_NO_DISPONIBLE` nunca aparece con un escenario activo.
- **El `Conflicto` del validador no es el de dominio.** Hay que mapearlo a `conflicto` +
  `conflicto_sesion` en la fase 5.
- **No uses `response_format={"type":"json_schema"}`** para la IA: no es portable entre proveedores.
- **`ortools` arrastra `pandas` y `numpy`.** Es inevitable; D-016 lo explica.
- **La generación devuelve `FACTIBLE`, no `OPTIMO`.** Es deliberado (D-020). No lo prometas como óptimo.

## Riesgos abiertos (nadie los verificó todavía)

1. **`PATCH /importaciones/{id}/filas`** solo se probó con un Excel sucio sintético, nunca contra el
   archivo real. Es el paso 3 del flujo de importación.
2. **Los 19 exports de Stitch no están en el repo.** `design/stitch/README.md` los lista con ID y
   viven en la nube de Stitch. La fase 6 necesita acceso a esa cuenta.
3. **Engram no persistió nada** durante las fases 2-4 (`project_transition_conflict`). **El repo es
   la única fuente de verdad.** No cuentes con memoria externa.
4. **`reportlab` no se probó** en la máquina del pitch. El PDF puede fallar por fuentes.

## Números de referencia

23 tablas · 11 códigos de conflicto · 20 decisiones · 182 tests · 120 sesiones de demo ·
generación 4.86 s · validación 1.7 ms.
