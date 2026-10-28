"""Conversores `db -> domain` y `domain -> db`.

Una sola pareja de funciones para las 23 tablas: los nombres de campo del modelo y de
la dataclass son idénticos (`DOMAIN.md` es la fuente de verdad de ambos), así que el
mapeo se resuelve por introspección y no hay 23 conversores que se desincronicen.
`tests/test_converters.py` verifica esa igualdad campo a campo; si alguien agrega una
columna sin su campo de dominio, el test falla antes de que el dato se pierda.

Para agregar una entidad: crear el modelo, la dataclass y una línea en `PARES`.
"""

import dataclasses
from typing import Any, TypeVar

from app.domain.carga import AsignacionCarga, DisponibilidadBloqueo
from app.domain.catalogo import (
    Aptitud,
    Asignatura,
    Bloque,
    Curso,
    Docente,
    Grado,
    Institucion,
)
from app.domain.conflictos import (
    Conflicto,
    ConflictoSesion,
    PropuestaCambio,
    PropuestaResolucion,
)
from app.domain.horario import Escenario, EscenarioCambio, HorarioVersion, Sesion
from app.domain.procesos import (
    EjecucionSolver,
    HistorialCambio,
    Importacion,
    ImportacionError,
)
from app.domain.recursos import Recurso, TipoRecurso
from app.models.base import Base
from app.models.carga import AsignacionCargaDB, DisponibilidadBloqueoDB
from app.models.catalogo import (
    AptitudDB,
    AsignaturaDB,
    BloqueDB,
    CursoDB,
    DocenteDB,
    GradoDB,
    InstitucionDB,
)
from app.models.conflictos import (
    ConflictoDB,
    ConflictoSesionDB,
    PropuestaCambioDB,
    PropuestaResolucionDB,
)
from app.models.historial import HistorialCambioDB
from app.models.horario import (
    EscenarioCambioDB,
    EscenarioDB,
    HorarioVersionDB,
    SesionDB,
)
from app.models.procesos import (
    EjecucionSolverDB,
    ImportacionDB,
    ImportacionErrorDB,
)
from app.models.recursos import RecursoDB, TipoRecursoDB

M = TypeVar("M", bound=Base)
D = TypeVar("D")

#: Parejas (modelo SQLAlchemy, dataclass de dominio). Orden = orden de `DOMAIN.md`.
PARES: tuple[tuple[type[Base], type], ...] = (
    (InstitucionDB, Institucion),
    (GradoDB, Grado),
    (CursoDB, Curso),
    (BloqueDB, Bloque),
    (AsignaturaDB, Asignatura),
    (DocenteDB, Docente),
    (AptitudDB, Aptitud),
    (TipoRecursoDB, TipoRecurso),
    (RecursoDB, Recurso),
    (AsignacionCargaDB, AsignacionCarga),
    (DisponibilidadBloqueoDB, DisponibilidadBloqueo),
    (EscenarioDB, Escenario),
    (EscenarioCambioDB, EscenarioCambio),
    (HorarioVersionDB, HorarioVersion),
    (SesionDB, Sesion),
    (ConflictoDB, Conflicto),
    (ConflictoSesionDB, ConflictoSesion),
    (PropuestaResolucionDB, PropuestaResolucion),
    (PropuestaCambioDB, PropuestaCambio),
    (EjecucionSolverDB, EjecucionSolver),
    (ImportacionDB, Importacion),
    (ImportacionErrorDB, ImportacionError),
    (HistorialCambioDB, HistorialCambio),
)

_DOMINIO = dict(PARES)
_MODELO = {entidad: modelo for modelo, entidad in PARES}

#: Columnas que el mixin rellena solo: no se escriben en NULL (romperían el NOT NULL).
_MARCAS = ("created_at", "updated_at")


def a_dominio[M: Base, D](fila: M) -> D:
    """Modelo (o fila) -> dataclass inmutable del dominio."""
    entidad = _DOMINIO.get(type(fila))
    if entidad is None:
        raise TypeError(f"Sin entidad de dominio para {type(fila).__name__}")
    campos = {campo.name: getattr(fila, campo.name) for campo in dataclasses.fields(entidad)}
    return entidad(**campos)


def a_modelo[M: Base, D](entidad: D) -> M:
    """Dataclass del dominio -> instancia del modelo (sin persistir)."""
    modelo = _MODELO.get(type(entidad))
    if modelo is None:
        raise TypeError(f"Sin modelo SQLAlchemy para {type(entidad).__name__}")

    datos: dict[str, Any] = {}
    for columna in modelo.__table__.columns:
        if not hasattr(entidad, columna.name):
            continue
        valor = getattr(entidad, columna.name)
        if valor is None and columna.name in _MARCAS:
            continue
        datos[columna.name] = valor
    return modelo(**datos)
