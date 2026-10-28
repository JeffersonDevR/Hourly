"""Conflictos del validador y propuestas de resolución.

Política de borrado (D-011): `conflicto_sesion` cuelga con CASCADE de `conflicto` y de
`sesion`. Sin eso, borrar una sesión con conflictos lanza `IntegrityError` en cuanto
`PRAGMA foreign_keys=ON` está activo. `propuesta_resolucion` también cae con su
conflicto: `validar` borra y regenera conflictos, y una propuesta huérfana no se puede
mostrar.
"""

import uuid
from datetime import datetime
from typing import Any

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.enums import (
    EstadoConflicto,
    EstadoPropuesta,
    Gravedad,
    OrigenPropuesta,
    TipoCambioPropuesta,
)
from app.models.base import Base, TimestampMixin, enum_column, utcnow


class ConflictoDB(TimestampMixin, Base):
    __tablename__ = "conflicto"

    id: Mapped[uuid.UUID] = mapped_column(sa.Uuid, primary_key=True, default=uuid.uuid4)
    horario_version_id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid, sa.ForeignKey("horario_version.id")
    )
    codigo: Mapped[str] = mapped_column(sa.String(64))
    gravedad: Mapped[Gravedad] = mapped_column(
        enum_column(Gravedad, nombre="ck_conflicto_gravedad")
    )
    estado: Mapped[EstadoConflicto] = mapped_column(
        enum_column(EstadoConflicto, nombre="ck_conflicto_estado")
    )
    mensaje: Mapped[str] = mapped_column(sa.Text)
    # jsonb en el diseño original; `sa.JSON` lo mantiene portable (D-001).
    detalle: Mapped[dict[str, Any] | None] = mapped_column(sa.JSON)
    detectado_at: Mapped[datetime] = mapped_column(sa.DateTime, default=utcnow)


class ConflictoSesionDB(TimestampMixin, Base):
    """Sesiones afectadas por un conflicto. PK compuesta, ambos lados en CASCADE (D-011)."""

    __tablename__ = "conflicto_sesion"

    conflicto_id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid, sa.ForeignKey("conflicto.id", ondelete="CASCADE"), primary_key=True
    )
    sesion_id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid, sa.ForeignKey("sesion.id", ondelete="CASCADE"), primary_key=True
    )


class PropuestaResolucionDB(TimestampMixin, Base):
    __tablename__ = "propuesta_resolucion"

    id: Mapped[uuid.UUID] = mapped_column(sa.Uuid, primary_key=True, default=uuid.uuid4)
    conflicto_id: Mapped[uuid.UUID | None] = mapped_column(
        sa.Uuid, sa.ForeignKey("conflicto.id", ondelete="CASCADE")
    )
    origen: Mapped[OrigenPropuesta] = mapped_column(
        enum_column(OrigenPropuesta, nombre="ck_propuesta_resolucion_origen")
    )
    titulo: Mapped[str] = mapped_column(sa.String(200))
    explicacion: Mapped[str] = mapped_column(sa.Text)
    impacto: Mapped[str | None] = mapped_column(sa.Text)
    estado: Mapped[EstadoPropuesta] = mapped_column(
        enum_column(EstadoPropuesta, nombre="ck_propuesta_resolucion_estado")
    )


class PropuestaCambioDB(TimestampMixin, Base):
    """Un cambio concreto ('mover la sesión X a martes B3') dentro de una propuesta.

    `sesion_id`/`asignacion_carga_id` son SET NULL: la propuesta puede sobrevivir a que
    se borre la sesión que proponía mover, y el cambio queda como dato histórico.
    """

    __tablename__ = "propuesta_cambio"

    id: Mapped[uuid.UUID] = mapped_column(sa.Uuid, primary_key=True, default=uuid.uuid4)
    propuesta_id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid, sa.ForeignKey("propuesta_resolucion.id", ondelete="CASCADE")
    )
    tipo: Mapped[TipoCambioPropuesta] = mapped_column(
        enum_column(TipoCambioPropuesta, nombre="ck_propuesta_cambio_tipo")
    )
    sesion_id: Mapped[uuid.UUID | None] = mapped_column(
        sa.Uuid, sa.ForeignKey("sesion.id", ondelete="SET NULL")
    )
    asignacion_carga_id: Mapped[uuid.UUID | None] = mapped_column(
        sa.Uuid, sa.ForeignKey("asignacion_carga.id", ondelete="SET NULL")
    )
    datos: Mapped[dict[str, Any]] = mapped_column(sa.JSON)
