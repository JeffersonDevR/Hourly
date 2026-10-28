"""Conversores `db <-> domain`: identidad, `jsonb` y paridad de campos.

La paridad campo a campo es lo que hace seguro el mapeo por introspección: si alguien
agrega una columna al modelo y olvida el campo de dominio, el dato se perdería en
silencio. Acá falla con nombre y apellido.
"""

import dataclasses
import uuid

import pytest
from sqlalchemy.orm import Session

from app.domain.conflictos import Conflicto
from app.domain.enums import EstadoConflicto, Gravedad
from app.models import Base
from app.models.converters import PARES, a_dominio, a_modelo
from app.repositories.conflictos import RepositorioConflicto
from tests.factories import BaseHorario, crear_base_horario


@pytest.fixture
def base(sesion_db: Session) -> BaseHorario:
    return crear_base_horario(sesion_db)


def test_todas_las_tablas_tienen_entidad_de_dominio() -> None:
    assert {modelo.__tablename__ for modelo, _ in PARES} == set(Base.metadata.tables)


@pytest.mark.parametrize(
    ("modelo", "entidad"),
    PARES,
    ids=[modelo.__tablename__ for modelo, _ in PARES],
)
def test_campos_de_dominio_y_columnas_coinciden(modelo: type, entidad: type) -> None:
    columnas = {columna.name for columna in modelo.__table__.columns}
    campos = {campo.name for campo in dataclasses.fields(entidad)}
    assert campos == columnas


def test_dominio_es_inmutable() -> None:
    conflicto = Conflicto(
        horario_version_id=uuid.uuid4(),
        codigo="X",
        gravedad=Gravedad.error,
        mensaje="m",
    )
    with pytest.raises(dataclasses.FrozenInstanceError):
        conflicto.mensaje = "otro"


def test_ida_y_vuelta_conserva_identidad_y_jsonb(
    sesion_db: Session, base: BaseHorario
) -> None:
    detalle = {
        "franja": {"dia": 2, "bloque": "B3"},
        "docentes": ["D1", "D3"],
        "anidado": [1, 2.5, None, True],
        "mensaje": "D1 ya tiene clase en esa franja",
    }
    original = Conflicto(
        horario_version_id=base.version.id,
        codigo="DOCENTE_DOBLE",
        gravedad=Gravedad.error,
        mensaje="D1 está en dos sesiones el martes B3",
        estado=EstadoConflicto.abierto,
        detalle=detalle,
    )
    repositorio = RepositorioConflicto(sesion_db)
    guardado = repositorio.agregar(original)

    sesion_db.expunge_all()
    leido = repositorio.obtener(original.id)

    assert leido is not None
    assert leido.id == original.id == guardado.id
    assert leido.detalle == detalle
    assert leido.gravedad is Gravedad.error
    assert leido.created_at is not None
    # El id que genera la DB es el de la dataclass: nadie lo reescribe después.
    assert leido.horario_version_id == base.version.id

    # domain -> db -> domain: la identidad y el payload sobreviven a la segunda vuelta.
    devuelta = a_dominio(a_modelo(leido))
    assert devuelta == leido


def test_id_generado_en_python_se_conserva(sesion_db: Session, base: BaseHorario) -> None:
    original = Conflicto(
        horario_version_id=base.version.id,
        codigo="MALLA_INCUMPLIDA",
        gravedad=Gravedad.advertencia,
        mensaje="faltan sesiones por colocar",
    )
    guardado = RepositorioConflicto(sesion_db).agregar(original)

    assert guardado.id == original.id
    assert guardado.detalle is None
