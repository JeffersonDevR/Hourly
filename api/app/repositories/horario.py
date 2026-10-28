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

    def obtener_por_nombre(self, nombre: str) -> Escenario | None:
        """Clave natural del upsert: `escenario` no tiene UNIQUE(nombre) en la DB."""
        fila = self.sesion.scalars(
            sa.select(EscenarioDB).where(EscenarioDB.nombre == nombre)
        ).first()
        return None if fila is None else a_dominio(fila)


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

    def obtener_por_franja(
        self, escenario_id: uuid.UUID, docente_id: uuid.UUID, dia: int, bloque_id: uuid.UUID
    ) -> EscenarioCambio | None:
        """Clave natural del overlay: (escenario, docente, día, bloque) (D-005, D-009)."""
        fila = self.sesion.scalars(
            sa.select(EscenarioCambioDB).where(
                EscenarioCambioDB.escenario_id == escenario_id,
                EscenarioCambioDB.docente_id == docente_id,
                EscenarioCambioDB.dia == dia,
                EscenarioCambioDB.bloque_id == bloque_id,
            )
        ).first()
        return None if fila is None else a_dominio(fila)
