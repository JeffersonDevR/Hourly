"""Tipos de recurso y recursos físicos."""

import uuid

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class TipoRecursoDB(TimestampMixin, Base):
    """Catálogo por código (GENERAL, LAB_CIENCIAS, CANCHA, SALA_INFORMATICA)."""

    __tablename__ = "tipo_recurso"

    codigo: Mapped[str] = mapped_column(sa.String(32), primary_key=True)


class RecursoDB(TimestampMixin, Base):
    __tablename__ = "recurso"
    __table_args__ = (sa.UniqueConstraint("codigo", name="uq_recurso_codigo"),)

    id: Mapped[uuid.UUID] = mapped_column(sa.Uuid, primary_key=True, default=uuid.uuid4)
    codigo: Mapped[str] = mapped_column(sa.String(32))
    nombre: Mapped[str] = mapped_column(sa.String(120))
    tipo_recurso: Mapped[str] = mapped_column(
        sa.String(32), sa.ForeignKey("tipo_recurso.codigo")
    )
    capacidad: Mapped[int] = mapped_column(sa.Integer)
    # 'Aula 7A' es el aula titular de 7A; el resto de recursos no tiene titular.
    curso_titular_id: Mapped[uuid.UUID | None] = mapped_column(
        sa.Uuid, sa.ForeignKey("curso.id")
    )
