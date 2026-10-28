"""Repositorios de catÃ¡logos.

Las bÃºsquedas por clave natural (`codigo`, `nombre`) existen porque D-009 define el
upsert de importaciÃ³n sobre ellas.
"""

import uuid

import sqlalchemy as sa

from app.domain.catalogo import (
    Aptitud,
    Asignatura,
    Bloque,
    Curso,
    Docente,
    Grado,
    Institucion,
)
from app.models.catalogo import (
    AptitudDB,
    AsignaturaDB,
    BloqueDB,
    CursoDB,
    DocenteDB,
    GradoDB,
    InstitucionDB,
)
from app.models.converters import a_dominio
from app.repositories.base import Repositorio, RepositorioCodigo


class RepositorioInstitucion(Repositorio[InstitucionDB, Institucion, uuid.UUID]):
    modelo = InstitucionDB


class RepositorioGrado(Repositorio[GradoDB, Grado, uuid.UUID]):
    modelo = GradoDB


class RepositorioCurso(RepositorioCodigo[CursoDB, Curso]):
    modelo = CursoDB


class RepositorioBloque(RepositorioCodigo[BloqueDB, Bloque]):
    modelo = BloqueDB


class RepositorioDocente(RepositorioCodigo[DocenteDB, Docente]):
    modelo = DocenteDB


class RepositorioAsignatura(Repositorio[AsignaturaDB, Asignatura, uuid.UUID]):
    modelo = AsignaturaDB

    def obtener_por_nombre(self, nombre: str) -> Asignatura | None:
        fila = self.sesion.scalars(
            sa.select(AsignaturaDB).where(AsignaturaDB.nombre == nombre)
        ).first()
        return None if fila is None else a_dominio(fila)


class RepositorioAptitud(Repositorio[AptitudDB, Aptitud, tuple[uuid.UUID, uuid.UUID]]):
    """La clave es la pareja (docente_id, asignatura_id)."""

    modelo = AptitudDB

    def listar_por_docente(self, docente_id: uuid.UUID) -> list[Aptitud]:
        filas = self.sesion.scalars(
            sa.select(AptitudDB).where(AptitudDB.docente_id == docente_id)
        ).all()
        return [a_dominio(fila) for fila in filas]
