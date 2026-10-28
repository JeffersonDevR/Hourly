"""Dominio: dataclasses inmutables del modelo de `docs/DOMAIN.md`.

Este paquete NO importa SQLAlchemy ni FastAPI: es el lenguaje común del validador,
el solver, la IA y los conversores. La persistencia vive en `app.models`.
"""

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
from app.domain.enums import (
    EstadoConflicto,
    EstadoPropuesta,
    EstadoVersion,
    Gravedad,
    ModoDocente,
    OrigenBloqueo,
    OrigenPropuesta,
    TipoBloque,
    TipoCambioPropuesta,
)
from app.domain.horario import Escenario, EscenarioCambio, HorarioVersion, Sesion
from app.domain.procesos import (
    EjecucionSolver,
    HistorialCambio,
    Importacion,
    ImportacionError,
)
from app.domain.recursos import Recurso, TipoRecurso

__all__ = [
    "Aptitud",
    "AsignacionCarga",
    "Asignatura",
    "Bloque",
    "Conflicto",
    "ConflictoSesion",
    "Curso",
    "DisponibilidadBloqueo",
    "Docente",
    "EjecucionSolver",
    "Escenario",
    "EscenarioCambio",
    "EstadoConflicto",
    "EstadoPropuesta",
    "EstadoVersion",
    "Grado",
    "Gravedad",
    "HistorialCambio",
    "HorarioVersion",
    "Importacion",
    "ImportacionError",
    "Institucion",
    "ModoDocente",
    "OrigenBloqueo",
    "OrigenPropuesta",
    "PropuestaCambio",
    "PropuestaResolucion",
    "Recurso",
    "Sesion",
    "TipoBloque",
    "TipoCambioPropuesta",
    "TipoRecurso",
]
