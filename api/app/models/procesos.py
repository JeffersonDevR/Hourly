"""Procesos: ejecuciones del solver e importaciones de Excel."""

import uuid
from datetime import datetime
from typing import Any

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.enums import Gravedad, ModoDocente
from app.models.base import Base, TimestampMixin, enum_column, utcnow


class EjecucionSolverDB(TimestampMixin, Base):
    __tablename__ = "ejecucion_solver"

    id: Mapped[uuid.UUID] = mapped_column(sa.Uuid, primary_key=True, default=uuid.uuid4)
    # NULL: diagnosticar_carga puede correr sin una versión concreta (D-007).
    horario_version_id: Mapped[uuid.UUID | None] = mapped_column(
        sa.Uuid, sa.ForeignKey("horario_version.id")
    )
    modo_docente: Mapped[ModoDocente] = mapped_column(
        enum_column(ModoDocente, nombre="ck_ejecucion_solver_modo_docente")
    )
    estado: Mapped[str] = mapped_column(sa.String(32))
    diagnostico: Mapped[dict[str, Any] | None] = mapped_column(sa.JSON)
    iniciado_at: Mapped[datetime] = mapped_column(sa.DateTime, default=utcnow)
    terminado_at: Mapped[datetime | None] = mapped_column(sa.DateTime)


class ImportacionDB(TimestampMixin, Base):
    __tablename__ = "importacion"

    id: Mapped[uuid.UUID] = mapped_column(sa.Uuid, primary_key=True, default=uuid.uuid4)
    archivo_nombre: Mapped[str] = mapped_column(sa.String(255))
    estado: Mapped[str] = mapped_column(sa.String(32))
    resumen: Mapped[dict[str, Any] | None] = mapped_column(sa.JSON)


class ImportacionErrorDB(TimestampMixin, Base):
    __tablename__ = "importacion_error"

    id: Mapped[uuid.UUID] = mapped_column(sa.Uuid, primary_key=True, default=uuid.uuid4)
    importacion_id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid, sa.ForeignKey("importacion.id", ondelete="CASCADE")
    )
    hoja: Mapped[str | None] = mapped_column(sa.String(120))
    fila: Mapped[int | None] = mapped_column(sa.Integer)
    columna: Mapped[str | None] = mapped_column(sa.String(120))
    severidad: Mapped[Gravedad] = mapped_column(
        enum_column(Gravedad, nombre="ck_importacion_error_severidad")
    )
    codigo: Mapped[str | None] = mapped_column(sa.String(64))
    mensaje: Mapped[str] = mapped_column(sa.Text)
    corregido: Mapped[bool] = mapped_column(
        sa.Boolean, nullable=False, default=False, server_default=sa.false()
    )
