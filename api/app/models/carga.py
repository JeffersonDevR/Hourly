"""Carga académica y disponibilidad base del docente."""

import uuid

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.enums import OrigenBloqueo
from app.models.base import Base, TimestampMixin, enum_column


class AsignacionCargaDB(TimestampMixin, Base):
    """Sesiones semanales que un curso necesita de una asignatura (UNIQUE por curso+asignatura)."""

    __tablename__ = "asignacion_carga"
    __table_args__ = (
        sa.UniqueConstraint(
            "curso_id", "asignatura_id", name="uq_asignacion_carga_curso_asignatura"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(sa.Uuid, primary_key=True, default=uuid.uuid4)
    curso_id: Mapped[uuid.UUID] = mapped_column(sa.Uuid, sa.ForeignKey("curso.id"))
    asignatura_id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid, sa.ForeignKey("asignatura.id")
    )
    docente_principal_id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid, sa.ForeignKey("docente.id")
    )
    sesiones_semana: Mapped[int] = mapped_column(sa.SmallInteger)
    tipo_recurso_requerido: Mapped[str] = mapped_column(
        sa.String(32), sa.ForeignKey("tipo_recurso.codigo")
    )


class DisponibilidadBloqueoDB(TimestampMixin, Base):
    """Franja NO disponible del docente.

    Es el estado base: los escenarios viven en `escenario_cambio` (D-005).
    """

    __tablename__ = "disponibilidad_bloqueo"
    __table_args__ = (
        sa.UniqueConstraint(
            "docente_id", "dia", "bloque_id", name="uq_disponibilidad_docente_dia_bloque"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(sa.Uuid, primary_key=True, default=uuid.uuid4)
    docente_id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid, sa.ForeignKey("docente.id", ondelete="CASCADE")
    )
    # 1=lunes … 5=viernes (DOMAIN.md).
    dia: Mapped[int] = mapped_column(sa.SmallInteger)
    bloque_id: Mapped[uuid.UUID] = mapped_column(sa.Uuid, sa.ForeignKey("bloque.id"))
    origen: Mapped[OrigenBloqueo] = mapped_column(
        enum_column(OrigenBloqueo, nombre="ck_disponibilidad_bloqueo_origen")
    )
    detalle: Mapped[str | None] = mapped_column(sa.Text)
