"""Repositorios: acceso a datos por agregado, sin reglas de negocio.

Cada repositorio recibe la `Session` y no hace `commit()`; la transacción es de quien
llama. Todos devuelven dataclasses de `app.domain`, nunca modelos SQLAlchemy.
"""

from app.repositories.base import Repositorio, RepositorioCodigo
from app.repositories.carga import RepositorioAsignacionCarga, RepositorioDisponibilidad
from app.repositories.catalogo import (
    RepositorioAptitud,
    RepositorioAsignatura,
    RepositorioBloque,
    RepositorioCurso,
    RepositorioDocente,
    RepositorioGrado,
    RepositorioInstitucion,
)
from app.repositories.conflictos import (
    RepositorioConflicto,
    RepositorioConflictoSesion,
    RepositorioPropuesta,
    RepositorioPropuestaCambio,
)
from app.repositories.horario import (
    RepositorioEscenario,
    RepositorioEscenarioCambio,
    RepositorioHorarioVersion,
    RepositorioSesion,
)
from app.repositories.procesos import (
    RepositorioEjecucionSolver,
    RepositorioHistorial,
    RepositorioImportacion,
    RepositorioImportacionError,
)
from app.repositories.recursos import RepositorioRecurso, RepositorioTipoRecurso

__all__ = [
    "Repositorio",
    "RepositorioAptitud",
    "RepositorioAsignacionCarga",
    "RepositorioAsignatura",
    "RepositorioBloque",
    "RepositorioCodigo",
    "RepositorioConflicto",
    "RepositorioConflictoSesion",
    "RepositorioCurso",
    "RepositorioDisponibilidad",
    "RepositorioDocente",
    "RepositorioEjecucionSolver",
    "RepositorioEscenario",
    "RepositorioEscenarioCambio",
    "RepositorioGrado",
    "RepositorioHistorial",
    "RepositorioHorarioVersion",
    "RepositorioImportacion",
    "RepositorioImportacionError",
    "RepositorioInstitucion",
    "RepositorioPropuesta",
    "RepositorioPropuestaCambio",
    "RepositorioRecurso",
    "RepositorioSesion",
    "RepositorioTipoRecurso",
]
