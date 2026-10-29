"""Traza de cambios para deshacer/rehacer.

La escribe únicamente `app.services.historial`; ningún router toca esta tabla.
`entidad_id` es texto (no `sa.Uuid`) porque apunta a PKs heterogéneas: `uuid` en casi
todas las tablas, pero `tipo_recurso.codigo` es un string ('GENERAL').
"""

import uuid
from datetime import datetime
from typing import Any

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, utcnow


class HistorialCambioDB(TimestampMixin, Base):
    __tablename__ = "historial_cambio"

    id: Mapped[uuid.UUID] = mapped_column(sa.Uuid, primary_key=True, default=uuid.uuid4)
    # NULL: hay cambios que no pertenecen a una versión (catálogos).
    horario_version_id: Mapped[uuid.UUID | None] = mapped_column(
        sa.Uuid, sa.ForeignKey("horario_version.id")
    )
    entidad: Mapped[str] = mapped_column(sa.String(64))
    entidad_id: Mapped[str] = mapped_column(sa.String(64))
    accion: Mapped[str] = mapped_column(sa.String(32))
    antes: Mapped[dict[str, Any] | None] = mapped_column(sa.JSON)
    despues: Mapped[dict[str, Any] | None] = mapped_column(sa.JSON)
    ocurrido_at: Mapped[datetime] = mapped_column(sa.DateTime, default=utcnow)
    # Pila de rehacer: `deshacer` la marca, `rehacer` la devuelve a False.
    deshecho: Mapped[bool] = mapped_column(
        sa.Boolean, nullable=False, default=False, server_default=sa.false()
    )
