"""Entorno de migraciones Alembic.

`render_as_batch=True` es obligatorio en SQLite: no soporta `ALTER TABLE` completo (D-001).
`target_metadata` es `Base.metadata` de `app.models`, la única fuente del esquema.
"""

from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine, pool

import app.db  # noqa: F401  # registra los PRAGMAs (FK, WAL) en toda conexión nueva
from app.config import get_settings
from app.models import Base

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

# Si un test o un script fija la URL en el Config, gana; si no, la de `app.config`.
DATABASE_URL = config.get_main_option("sqlalchemy.url") or get_settings().database_url


def run_migrations_offline() -> None:
    context.configure(
        url=DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    engine = create_engine(DATABASE_URL, poolclass=pool.NullPool)

    with engine.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
