"""Repositorios de conflictos y propuestas."""

import uuid

import sqlalchemy as sa

from app.domain.conflictos import (
    Conflicto,
    ConflictoSesion,
    PropuestaCambio,
    PropuestaResolucion,
)
from app.models.conflictos import (
    ConflictoDB,
    ConflictoSesionDB,
    PropuestaCambioDB,
    PropuestaResolucionDB,
)
from app.models.converters import a_dominio
from app.repositories.base import Repositorio


class RepositorioConflicto(Repositorio[ConflictoDB, Conflicto, uuid.UUID]):
    modelo = ConflictoDB

    def listar_por_version(self, horario_version_id: uuid.UUID) -> list[Conflicto]:
        filas = self.sesion.scalars(
            sa.select(ConflictoDB).where(
                ConflictoDB.horario_version_id == horario_version_id
            )
        ).all()
        return [a_dominio(fila) for fila in filas]


class RepositorioConflictoSesion(
    Repositorio[ConflictoSesionDB, ConflictoSesion, tuple[uuid.UUID, uuid.UUID]]
):
    """La clave es la pareja (conflicto_id, sesion_id)."""

    modelo = ConflictoSesionDB


class RepositorioPropuesta(Repositorio[PropuestaResolucionDB, PropuestaResolucion, uuid.UUID]):
    modelo = PropuestaResolucionDB


class RepositorioPropuestaCambio(
    Repositorio[PropuestaCambioDB, PropuestaCambio, uuid.UUID]
):
    modelo = PropuestaCambioDB

    def listar_por_propuesta(self, propuesta_id: uuid.UUID) -> list[PropuestaCambio]:
        filas = self.sesion.scalars(
            sa.select(PropuestaCambioDB).where(
                PropuestaCambioDB.propuesta_id == propuesta_id
            )
        ).all()
        return [a_dominio(fila) for fila in filas]
