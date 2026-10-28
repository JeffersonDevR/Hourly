"""Fixtures comunes: una DB SQLite temporal migrada con Alembic.

Reglas:
- Nunca se usa `houry.db` (el archivo de desarrollo) ni `data/Datos_prueba_Gnosoft.xlsx`.
- El esquema de los tests es el que produce `alembic upgrade head`, no `create_all()`:
  así una migración incompleta rompe los tests en vez de esconderse.
"""

from collections.abc import Iterator

import pytest
import sqlalchemy as sa
from sqlalchemy.orm import Session

from app.db import crear_engine
from tests.dbutil import migrar, url_sqlite


@pytest.fixture(scope="session")
def url_db(tmp_path_factory: pytest.TempPathFactory) -> str:
    ruta = tmp_path_factory.mktemp("houry-db") / "houry_test.db"
    return url_sqlite(ruta)


@pytest.fixture(scope="session")
def motor(url_db: str) -> Iterator[sa.Engine]:
    migrar(url_db)
    engine = crear_engine(url_db)
    yield engine
    engine.dispose()


@pytest.fixture
def sesion_db(motor: sa.Engine) -> Iterator[Session]:
    """Sesión por test dentro de una transacción externa que se revierte al final.

    Cada test empieza con la DB vacía y no deja rastro: el estado se crea en el test.

    `join_transaction_mode="rollback_only"` es obligatorio: los endpoints hacen
    `commit()` y con `create_savepoint` ese commit llegaría al archivo, dejando filas
    para el test siguiente. En este modo `commit()` solo hace `flush()` y la
    transacción externa (la del fixture) sigue siendo la única que decide.
    """
    conexion = motor.connect()
    transaccion = conexion.begin()
    sesion = Session(bind=conexion, join_transaction_mode="rollback_only")
    try:
        yield sesion
    finally:
        sesion.close()
        # Un IntegrityError intencional deja la transacción ya revertida por SQLAlchemy.
        if transaccion.is_active:
            transaccion.rollback()
        conexion.close()
