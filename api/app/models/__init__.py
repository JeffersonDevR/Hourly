"""Modelos SQLAlchemy 2 del esquema de `docs/DOMAIN.md`.

Importar este paquete registra TODAS las tablas en `Base.metadata`, que es lo que
Alembic migra. Los conversores a dominio se importan acá por comodidad:
`from app.models import a_dominio, a_modelo`.
"""

from app.models.base import Base, TimestampMixin, enum_column, utcnow
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
from app.models.converters import PARES, a_dominio, a_modelo
from app.models.historial import HistorialCambioDB
from app.models.horario import (
    EscenarioCambioDB,
    EscenarioDB,
    HorarioVersionDB,
    SesionDB,
)
from app.models.procesos import EjecucionSolverDB, ImportacionDB, ImportacionErrorDB
from app.models.recursos import RecursoDB, TipoRecursoDB

__all__ = [
    "PARES",
    "AptitudDB",
    "AsignacionCargaDB",
    "AsignaturaDB",
    "Base",
    "BloqueDB",
    "ConflictoDB",
    "ConflictoSesionDB",
    "CursoDB",
    "DisponibilidadBloqueoDB",
    "DocenteDB",
    "EjecucionSolverDB",
    "EscenarioCambioDB",
    "EscenarioDB",
    "GradoDB",
    "HistorialCambioDB",
    "HorarioVersionDB",
    "ImportacionDB",
    "ImportacionErrorDB",
    "InstitucionDB",
    "PropuestaCambioDB",
    "PropuestaResolucionDB",
    "RecursoDB",
    "SesionDB",
    "TipoRecursoDB",
    "TimestampMixin",
    "a_dominio",
    "a_modelo",
    "enum_column",
    "utcnow",
]
