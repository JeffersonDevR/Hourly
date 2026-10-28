"""Motor, fábrica de sesiones y PRAGMAs de SQLite (D-001).

`PRAGMA foreign_keys` se aplica en el evento `connect` de **todos** los `Engine`, no
solo en el de la app: si no, cualquier engine creado a mano (tests, Alembic, scripts)
tendría FKs decorativas y las invariantes duras del dominio no se validarían.
`journal_mode=WAL` y `busy_timeout` evitan el `database is locked` cuando la UI
consulta mientras el solver escribe.
"""

import sqlite3
from collections.abc import Iterator
from functools import lru_cache

import sqlalchemy as sa
from sqlalchemy import Engine, event
from sqlalchemy.orm import Session, sessionmaker

from app.config import get_settings

#: SQLite reintenta hasta 5 s antes de devolver "database is locked".
BUSY_TIMEOUT_MS = 5000


def crear_engine(url: str) -> Engine:
    """Engine SQLite. Cacheado por URL: una URL, un engine (y un solo pool)."""
    return _crear_engine(url)


@lru_cache(maxsize=8)
def _crear_engine(url: str) -> Engine:
    kwargs: dict[str, object] = {}
    if url.startswith("sqlite"):
        # FastAPI atiende cada request en su propio hilo.
        kwargs["connect_args"] = {"check_same_thread": False}
    return sa.create_engine(url, **kwargs)


@event.listens_for(Engine, "connect")
def _pragmas_sqlite(dbapi_connection: object, _registro: object) -> None:
    """PRAGMAs de cada conexión nueva. Ignora drivers que no son sqlite3."""
    if not isinstance(dbapi_connection, sqlite3.Connection):
        return
    cursor = dbapi_connection.cursor()
    try:
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute(f"PRAGMA busy_timeout={BUSY_TIMEOUT_MS}")
        cursor.execute("PRAGMA journal_mode=WAL")
    finally:
        cursor.close()


def get_engine() -> Engine:
    return crear_engine(get_settings().database_url)


def get_session_factory() -> sessionmaker[Session]:
    return sessionmaker(bind=get_engine(), expire_on_commit=False)


def get_session() -> Iterator[Session]:
    """Dependencia de FastAPI: una sesión por request, cerrada al final."""
    with get_session_factory()() as sesion:
        yield sesion
