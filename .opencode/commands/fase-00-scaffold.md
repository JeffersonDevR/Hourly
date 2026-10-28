---
description: Fase 0 — esqueleto del monorepo, demo.ps1, CI local
---
Lee AGENTS.md, docs/DOMAIN.md y docs/ARCHITECTURE.md.
Crea el esqueleto del proyecto:
- `api/` con FastAPI + uv (`pyproject.toml` con `name = "hourly-api"`), estructura de módulos de ARCHITECTURE.md (vacíos con `__init__.py`), `/api/estado` devolviendo `{ok:true, ai_disponible:false}`, config por env (`DATABASE_URL` con default `sqlite:///./hourly.db`, `AI_BASE_URL`, `AI_MODEL`, `AI_API_KEY`, `SOLVER_TIMEOUT_S`), ruff y pytest configurados.
- `web/` con Vite + React + TS strict + Tailwind + shadcn/ui + TanStack Query + react-router, con el layout (navegación lateral con las 9 rutas + "Próximamente: Usuarios y Vistas móviles", barra superior global con placeholders) y proxy a `/api`.
- `.env.example`, `demo.ps1` en la raíz y **sin `make`** (D-015). `demo.ps1` levanta API (:8000) + web (:5173), acepta `-Dev` (con `--reload`) y `-Check` (arranca, verifica `/api/estado` y baja todo), y mata el árbol de procesos al salir. Sin base externa: la DB es el archivo SQLite de `DATABASE_URL`.
- `docs/DECISIONS.md` solo si falta: nunca sobrescribirlo.
Comandos canónicos (no hay alias): `uv run --directory api pytest`, `uv run --directory api ruff check .`, `corepack pnpm --dir web typecheck`, `uv run --directory api alembic upgrade head`.
Criterios de aceptación: `.\demo.ps1 -Check` devuelve `ok=true ai_disponible=false` y deja los puertos 8000 y 5173 libres al terminar; pytest y ruff pasan; la web muestra el layout y llama a `/api/estado`.
$ARGUMENTS
