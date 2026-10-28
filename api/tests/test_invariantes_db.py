"""Invariantes DURAS en la DB: únicos de `sesion`, CASCADE y PRAGMAs.

Estos tests son la prueba de que la regla 4 de `AGENTS.md` no es decorativa: si el
listener de `PRAGMA foreign_keys=ON` no corriera, los tres primeros pasarían igual
(los UNIQUE los aplica el motor) pero el de CASCADE fallaría en silencio.
"""

import uuid

import pytest
import sqlalchemy as sa
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.domain.conflictos import Conflicto, ConflictoSesion
from app.domain.enums import Gravedad, TipoBloque
from app.models.conflictos import ConflictoSesionDB
from app.repositories.catalogo import RepositorioAsignatura
from app.repositories.conflictos import RepositorioConflicto, RepositorioConflictoSesion
from app.repositories.horario import RepositorioSesion
from tests.factories import BaseHorario, crear_base_horario, sesion_en_primera_franja


@pytest.fixture
def base(sesion_db: Session) -> BaseHorario:
    return crear_base_horario(sesion_db)


def test_pragma_foreign_keys_activo(sesion_db: Session) -> None:
    assert sesion_db.execute(sa.text("PRAGMA foreign_keys")).scalar_one() == 1


def test_pragmas_de_rendimiento(sesion_db: Session) -> None:
    """WAL y busy_timeout se aplican junto con el de FKs (D-001)."""
    assert sesion_db.execute(sa.text("PRAGMA journal_mode")).scalar_one().lower() == "wal"
    assert sesion_db.execute(sa.text("PRAGMA busy_timeout")).scalar_one() > 0


@pytest.mark.parametrize(
    ("caso", "columna"),
    [
        # Misma versión, día y bloque; cambia todo menos el docente.
        ("docente", "sesion.docente_id"),
        # Misma versión, día y bloque; cambia todo menos el curso.
        ("curso", "sesion.curso_id"),
        # Misma versión, día y bloque; cambia todo menos el recurso.
        ("recurso", "sesion.recurso_id"),
    ],
)
def test_sesion_no_admite_dos_veces_la_misma_franja(
    sesion_db: Session, base: BaseHorario, caso: str, columna: str
) -> None:
    repositorio = RepositorioSesion(sesion_db)
    repositorio.agregar(sesion_en_primera_franja(base))

    variantes = {
        "docente": dict(curso=base.curso_b, docente=base.docente_a, recurso=base.recurso_b),
        "curso": dict(curso=base.curso_a, docente=base.docente_b, recurso=base.recurso_b),
        "recurso": dict(curso=base.curso_b, docente=base.docente_b, recurso=base.recurso_a),
    }

    with pytest.raises(IntegrityError) as error:
        repositorio.agregar(sesion_en_primera_franja(base, **variantes[caso]))

    # El mensaje de SQLite nombra las columnas del índice violado: prueba que falla el
    # único correcto y no otro por casualidad.
    assert columna in str(error.value)


def test_otro_dia_es_otra_franja(sesion_db: Session, base: BaseHorario) -> None:
    """Control negativo: las mismas entidades en otro día NO chocan."""
    repositorio = RepositorioSesion(sesion_db)
    repositorio.agregar(sesion_en_primera_franja(base, dia=1))
    repositorio.agregar(sesion_en_primera_franja(base, dia=2))

    assert len(repositorio.listar_por_version(base.version.id)) == 2


def test_borrar_sesion_con_conflicto_no_falla_y_arrastra_el_vinculo(
    sesion_db: Session, base: BaseHorario
) -> None:
    sesion = RepositorioSesion(sesion_db).agregar(sesion_en_primera_franja(base))
    conflicto = RepositorioConflicto(sesion_db).agregar(
        Conflicto(
            horario_version_id=base.version.id,
            codigo="DOCENTE_DOBLE",
            gravedad=Gravedad.error,
            mensaje="D1 está en dos sesiones a la vez",
        )
    )
    RepositorioConflictoSesion(sesion_db).agregar(
        ConflictoSesion(conflicto_id=conflicto.id, sesion_id=sesion.id)
    )
    assert _vinculos(sesion_db) == 1

    # Sin ON DELETE CASCADE esto lanzaría IntegrityError (D-011).
    assert RepositorioSesion(sesion_db).eliminar(sesion.id) is True

    assert _vinculos(sesion_db) == 0
    # El conflicto no se borra: solo pierde la referencia a la sesión.
    assert RepositorioConflicto(sesion_db).obtener(conflicto.id) is not None


def test_borrar_conflicto_arrastra_sus_vinculos(
    sesion_db: Session, base: BaseHorario
) -> None:
    """El otro lado del CASCADE: `validar` borra y regenera conflictos (D-011)."""
    sesion = RepositorioSesion(sesion_db).agregar(sesion_en_primera_franja(base))
    conflicto = RepositorioConflicto(sesion_db).agregar(
        Conflicto(
            horario_version_id=base.version.id,
            codigo="CURSO_DOBLE",
            gravedad=Gravedad.error,
            mensaje="6A en dos sesiones a la vez",
        )
    )
    RepositorioConflictoSesion(sesion_db).agregar(
        ConflictoSesion(conflicto_id=conflicto.id, sesion_id=sesion.id)
    )

    assert RepositorioConflicto(sesion_db).eliminar(conflicto.id) is True

    assert _vinculos(sesion_db) == 0
    assert RepositorioSesion(sesion_db).obtener(sesion.id) is not None


def _vinculos(sesion_db: Session) -> int:
    return sesion_db.scalar(
        sa.select(sa.func.count()).select_from(ConflictoSesionDB)
    ) or 0


def test_enum_es_varchar_con_check(sesion_db: Session, base: BaseHorario) -> None:
    """El enum se guarda como texto y un valor fuera del catálogo no entra (D-001)."""
    assert base.bloque.tipo is TipoBloque.clase

    # INSERT crudo: por el ORM, `validate_strings` cortaría antes y no se probaría el CHECK.
    with pytest.raises(IntegrityError):
        sesion_db.execute(
            sa.text(
                "INSERT INTO bloque (id, codigo, orden, inicio, fin, duracion_min, tipo,"
                " created_at, updated_at) VALUES (:id, 'B9', 9, '09:00', '10:00', 60,"
                " 'recreo', '2026-01-01 00:00:00', '2026-01-01 00:00:00')"
            ).bindparams(id=uuid.uuid4().hex)
        )


def test_asignatura_es_pesada_por_defecto_false(
    sesion_db: Session, base: BaseHorario
) -> None:
    """D-006: la marca es blanda y arranca apagada."""
    guardada = RepositorioAsignatura(sesion_db).obtener(base.asignatura.id)

    assert guardada is not None
    assert guardada.es_pesada is False
