"""Repositorios de procesos (solver, importación) e historial."""

import uuid

import sqlalchemy as sa

from app.domain.procesos import (
    EjecucionSolver,
    HistorialCambio,
    Importacion,
    ImportacionError,
)
from app.models.converters import a_dominio
from app.models.historial import HistorialCambioDB
from app.models.procesos import EjecucionSolverDB, ImportacionDB, ImportacionErrorDB
from app.repositories.base import Repositorio

_SOLO_SERVICIO = (
    "historial_cambio se escribe solo con app.services.historial.registrar_cambio"
)


class RepositorioEjecucionSolver(
    Repositorio[EjecucionSolverDB, EjecucionSolver, uuid.UUID]
):
    modelo = EjecucionSolverDB


class RepositorioImportacion(Repositorio[ImportacionDB, Importacion, uuid.UUID]):
    modelo = ImportacionDB


class RepositorioImportacionError(
    Repositorio[ImportacionErrorDB, ImportacionError, uuid.UUID]
):
    modelo = ImportacionErrorDB

    def listar_por_importacion(
        self, importacion_id: uuid.UUID
    ) -> list[ImportacionError]:
        filas = self.sesion.scalars(
            sa.select(ImportacionErrorDB).where(
                ImportacionErrorDB.importacion_id == importacion_id
            )
        ).all()
        return [a_dominio(fila) for fila in filas]


class RepositorioHistorial(Repositorio[HistorialCambioDB, HistorialCambio, uuid.UUID]):
    """Solo lectura: el único escritor del historial es `app.services.historial`."""

    modelo = HistorialCambioDB

    def agregar(self, entidad: HistorialCambio) -> HistorialCambio:
        raise NotImplementedError(_SOLO_SERVICIO)

    def actualizar(self, entidad: HistorialCambio) -> HistorialCambio:
        raise NotImplementedError(_SOLO_SERVICIO)

    def eliminar(self, clave: uuid.UUID) -> bool:
        raise NotImplementedError(_SOLO_SERVICIO)

    def listar_por_version(
        self, horario_version_id: uuid.UUID
    ) -> list[HistorialCambio]:
        """Entradas de una versión, de la más vieja a la más nueva (orden de deshacer)."""
        filas = self.sesion.scalars(
            sa.select(HistorialCambioDB)
            .where(HistorialCambioDB.horario_version_id == horario_version_id)
            .order_by(HistorialCambioDB.ocurrido_at, HistorialCambioDB.created_at)
        ).all()
        return [a_dominio(fila) for fila in filas]
