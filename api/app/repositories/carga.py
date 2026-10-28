"""Repositorios de carga académica y disponibilidad base."""

import uuid

import sqlalchemy as sa

from app.domain.carga import AsignacionCarga, DisponibilidadBloqueo
from app.models.carga import AsignacionCargaDB, DisponibilidadBloqueoDB
from app.models.converters import a_dominio
from app.repositories.base import Repositorio


class RepositorioAsignacionCarga(
    Repositorio[AsignacionCargaDB, AsignacionCarga, uuid.UUID]
):
    modelo = AsignacionCargaDB

    def obtener_por_curso_asignatura(
        self, curso_id: uuid.UUID, asignatura_id: uuid.UUID
    ) -> AsignacionCarga | None:
        """Clave natural del upsert de importación: UNIQUE(curso_id, asignatura_id) (D-009)."""
        fila = self.sesion.scalars(
            sa.select(AsignacionCargaDB).where(
                AsignacionCargaDB.curso_id == curso_id,
                AsignacionCargaDB.asignatura_id == asignatura_id,
            )
        ).first()
        return None if fila is None else a_dominio(fila)

    def listar_por_curso(self, curso_id: uuid.UUID) -> list[AsignacionCarga]:
        filas = self.sesion.scalars(
            sa.select(AsignacionCargaDB).where(AsignacionCargaDB.curso_id == curso_id)
        ).all()
        return [a_dominio(fila) for fila in filas]


class RepositorioDisponibilidad(
    Repositorio[DisponibilidadBloqueoDB, DisponibilidadBloqueo, uuid.UUID]
):
    modelo = DisponibilidadBloqueoDB

    def listar_por_docente(self, docente_id: uuid.UUID) -> list[DisponibilidadBloqueo]:
        filas = self.sesion.scalars(
            sa.select(DisponibilidadBloqueoDB).where(
                DisponibilidadBloqueoDB.docente_id == docente_id
            )
        ).all()
        return [a_dominio(fila) for fila in filas]
