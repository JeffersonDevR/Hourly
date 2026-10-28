"""La migración inicial: `alembic upgrade head` sobre una base vacía.

Es el único test que corre Alembic por CLI, para probar exactamente el comando del
README/DECISIONS (D-015) y no una variante programática.
"""

from pathlib import Path

import sqlalchemy as sa

from app.models import Base
from tests.dbutil import migrar_por_cli, url_sqlite

TABLAS_CLAVE = {"sesion", "conflicto_sesion", "historial_cambio", "asignatura"}


def _tablas(url: str) -> set[str]:
    engine = sa.create_engine(url)
    try:
        return set(sa.inspect(engine).get_table_names())
    finally:
        engine.dispose()


def test_upgrade_head_desde_cero(tmp_path: Path) -> None:
    ruta = tmp_path / "desde_cero.db"
    url = url_sqlite(ruta)
    assert not ruta.exists()

    resultado = migrar_por_cli(url)

    assert resultado.returncode == 0, resultado.stderr
    tablas = _tablas(url)
    # La migración cubre TODO el esquema de los modelos, ni una tabla más ni una menos.
    assert tablas - {"alembic_version"} == set(Base.metadata.tables)
    assert tablas >= TABLAS_CLAVE


def test_migracion_crea_los_tres_unicos_de_sesion(tmp_path: Path) -> None:
    url = url_sqlite(tmp_path / "unicos.db")
    assert migrar_por_cli(url).returncode == 0

    engine = sa.create_engine(url)
    try:
        inspector = sa.inspect(engine)
        unicos = {
            (constraint["name"], tuple(constraint["column_names"]))
            for constraint in inspector.get_unique_constraints("sesion")
        }
        # Inspecciona la DB real, no los modelos: si la migración pierde un índice, falla acá.
        assert ("uq_sesion_docente_franja", (
            "horario_version_id", "dia", "bloque_id", "docente_id",
        )) in unicos
        assert ("uq_sesion_curso_franja", (
            "horario_version_id", "dia", "bloque_id", "curso_id",
        )) in unicos
        assert ("uq_sesion_recurso_franja", (
            "horario_version_id", "dia", "bloque_id", "recurso_id",
        )) in unicos
    finally:
        engine.dispose()


def test_borrado_en_cascada_de_conflicto_sesion(tmp_path: Path) -> None:
    """Las dos FKs de `conflicto_sesion` se crean con ON DELETE CASCADE (D-011)."""
    url = url_sqlite(tmp_path / "cascada.db")
    assert migrar_por_cli(url).returncode == 0

    engine = sa.create_engine(url)
    try:
        inspector = sa.inspect(engine)
        for fk in inspector.get_foreign_keys("conflicto_sesion"):
            assert fk["options"].get("ondelete") == "CASCADE", fk
    finally:
        engine.dispose()
