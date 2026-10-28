---
description: Fase 1 — modelos SQLAlchemy, migraciones Alembic e índices de invariantes
---
Implementa el modelo de docs/DOMAIN.md ("Tablas MVP") con SQLAlchemy 2 + Alembic.
- Enums con `native_enum=False` (VARCHAR + CHECK), FKs, UNIQUE y los índices únicos de `sesion` (incluido el parcial de `recurso_id`).
- PK `sa.Uuid` con UUID generado en Python (`default=uuid.uuid4`), nunca `server_default=text("gen_random_uuid()")`.
- `asignatura.es_pesada bool` (D-006) y `conflicto_sesion` con `ON DELETE CASCADE` hacia `sesion` y hacia `conflicto` (D-011).
- Listener de `connect` con `PRAGMA foreign_keys=ON`, más `journal_mode=WAL` y `busy_timeout` (D-001). Sin el PRAGMA, las FKs son decorativas.
- Alembic configurado con `render_as_batch=True` (SQLite no soporta `ALTER TABLE` completo).
- Repositorios simples por agregado y un conversor `db → domain` (dataclasses de `app/domain`) y `domain → db`.
- Tests sobre SQLite (sin contenedores): insertar dos sesiones del mismo docente/día/bloque falla; igual para curso y recurso; borrar una `sesion` que tiene un `conflicto` asociado no lanza.
- `historial_cambio` se escribe desde una capa de servicio, no desde los routers.
Criterios: `alembic upgrade head` limpio desde cero; tests de índices y de `ON DELETE CASCADE` en verde; `uv run --directory api ruff check .` limpio.
$ARGUMENTS
