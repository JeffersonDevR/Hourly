"""Repositorios de versiones de horario, sesiones y escenarios."""

import uuid

import sqlalchemy as sa

from app.domain.horario import Escenario, EscenarioCambio, HorarioVersion, Sesion
from app.models.converters import a_dominio
from app.models.horario import (
    EscenarioCambioDB,
    EscenarioDB,
    HorarioVersionDB,
    SesionDB,
)
from app.repositories.base import Repositorio


class RepositorioHorarioVersion(Repositorio[HorarioVersionDB, HorarioVersion, uuid.UUID]):
    modelo = HorarioVersionDB


class RepositorioSesion(Repositorio[SesionDB, Sesion, uuid.UUID]):
    modelo = SesionDB

    def listar_por_version(self, horario_version_id: uuid.UUID) -> list[Sesion]:
        filas = self.sesion.scalars(
            sa.select(SesionDB).where(SesionDB.horario_version_id == horario_version_id)
        ).all()
        return [a_dominio(fila) for fila in filas]


class RepositorioEscenario(Repositorio[EscenarioDB, Escenario, uuid.UUID]):
    modelo = EscenarioDB


class RepositorioEscenarioCambio(
    Repositorio[EscenarioCambioDB, EscenarioCambio, uuid.UUID]
):
    modelo = EscenarioCambioDB

    def listar_por_escenario(self, escenario_id: uuid.UUID) -> list[EscenarioCambio]:
        filas = self.sesion.scalars(
            sa.select(EscenarioCambioDB).where(
                EscenarioCambioDB.escenario_id == escenario_id
            )
        ).all()
        return [a_dominio(fila) for fila in filas]
