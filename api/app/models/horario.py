"""Versiones del horario, sesiones colocadas y el overlay de escenarios."""

import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.enums import EstadoVersion
from app.models.base import Base, TimestampMixin, enum_column


class EscenarioDB(TimestampMixin, Base):
    """'¿Y si...?' Sin columna `activo`: el escenario activo es el de la versión (D-010)."""

    __tablename__ = "escenario"

    id: Mapped[uuid.UUID] = mapped_column(sa.Uuid, primary_key=True, default=uuid.uuid4)
    nombre: Mapped[str] = mapped_column(sa.String(120))
    descripcion: Mapped[str | None] = mapped_column(sa.Text)


class HorarioVersionDB(TimestampMixin, Base):
    __tablename__ = "horario_version"

    id: Mapped[uuid.UUID] = mapped_column(sa.Uuid, primary_key=True, default=uuid.uuid4)
    numero: Mapped[int] = mapped_column(sa.Integer)
    estado: Mapped[EstadoVersion] = mapped_column(
        enum_column(EstadoVersion, nombre="ck_horario_version_estado")
    )
    escenario_id: Mapped[uuid.UUID | None] = mapped_column(
        sa.Uuid, sa.ForeignKey("escenario.id")
    )
    nota: Mapped[str | None] = mapped_column(sa.Text)
    publicado_at: Mapped[datetime | None] = mapped_column(sa.DateTime)


class SesionDB(TimestampMixin, Base):
    """Una asignación colocada en (día, bloque).

    Los tres UNIQUE son las invariantes DURAS del dominio: un docente, un curso o un
    recurso no pueden estar dos veces en la misma franja de la misma versión.
    El índice de `recurso_id` no es parcial: en SQLite y en Postgres NULL ≠ NULL, así
    que las sesiones sin recurso no colisionan entre sí (D-001).
    """

    __tablename__ = "sesion"
    __table_args__ = (
        sa.UniqueConstraint(
            "horario_version_id", "dia", "bloque_id", "docente_id",
            name="uq_sesion_docente_franja",
        ),
        sa.UniqueConstraint(
            "horario_version_id", "dia", "bloque_id", "curso_id",
            name="uq_sesion_curso_franja",
        ),
        sa.UniqueConstraint(
            "horario_version_id", "dia", "bloque_id", "recurso_id",
            name="uq_sesion_recurso_franja",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(sa.Uuid, primary_key=True, default=uuid.uuid4)
    horario_version_id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid, sa.ForeignKey("horario_version.id")
    )
    asignacion_carga_id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid, sa.ForeignKey("asignacion_carga.id")
    )
    curso_id: Mapped[uuid.UUID] = mapped_column(sa.Uuid, sa.ForeignKey("curso.id"))
    docente_id: Mapped[uuid.UUID] = mapped_column(sa.Uuid, sa.ForeignKey("docente.id"))
    recurso_id: Mapped[uuid.UUID | None] = mapped_column(
        sa.Uuid, sa.ForeignKey("recurso.id")
    )
    dia: Mapped[int] = mapped_column(sa.SmallInteger)
    bloque_id: Mapped[uuid.UUID] = mapped_column(sa.Uuid, sa.ForeignKey("bloque.id"))


class EscenarioCambioDB(TimestampMixin, Base):
    """Overlay de disponibilidad: SOLO existe dentro de un escenario (D-005)."""

    __tablename__ = "escenario_cambio"

    id: Mapped[uuid.UUID] = mapped_column(sa.Uuid, primary_key=True, default=uuid.uuid4)
    escenario_id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid, sa.ForeignKey("escenario.id", ondelete="CASCADE")
    )
    docente_id: Mapped[uuid.UUID] = mapped_column(sa.Uuid, sa.ForeignKey("docente.id"))
    dia: Mapped[int] = mapped_column(sa.SmallInteger)
    bloque_id: Mapped[uuid.UUID] = mapped_column(sa.Uuid, sa.ForeignKey("bloque.id"))
    disponible_nuevo: Mapped[bool] = mapped_column(sa.Boolean, nullable=False)
    motivo: Mapped[str | None] = mapped_column(sa.Text)
