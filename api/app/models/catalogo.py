"""Catálogos base: institución, grados, cursos, bloques, asignaturas y docentes."""

import uuid
from datetime import time

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.enums import TipoBloque
from app.models.base import Base, TimestampMixin, enum_column


class InstitucionDB(TimestampMixin, Base):
    __tablename__ = "institucion"

    id: Mapped[uuid.UUID] = mapped_column(sa.Uuid, primary_key=True, default=uuid.uuid4)
    nombre: Mapped[str] = mapped_column(sa.String(120))
    logo_url: Mapped[str | None] = mapped_column(sa.Text)
    color_acento: Mapped[str | None] = mapped_column(sa.String(16))


class GradoDB(TimestampMixin, Base):
    __tablename__ = "grado"

    id: Mapped[uuid.UUID] = mapped_column(sa.Uuid, primary_key=True, default=uuid.uuid4)
    nombre: Mapped[str] = mapped_column(sa.String(60))
    orden: Mapped[int] = mapped_column(sa.Integer)


class CursoDB(TimestampMixin, Base):
    __tablename__ = "curso"
    __table_args__ = (sa.UniqueConstraint("codigo", name="uq_curso_codigo"),)

    id: Mapped[uuid.UUID] = mapped_column(sa.Uuid, primary_key=True, default=uuid.uuid4)
    codigo: Mapped[str] = mapped_column(sa.String(32))
    nombre: Mapped[str] = mapped_column(sa.String(120))
    grado_id: Mapped[uuid.UUID] = mapped_column(sa.Uuid, sa.ForeignKey("grado.id"))
    estudiantes: Mapped[int] = mapped_column(sa.Integer)


class BloqueDB(TimestampMixin, Base):
    __tablename__ = "bloque"
    __table_args__ = (sa.UniqueConstraint("codigo", name="uq_bloque_codigo"),)

    id: Mapped[uuid.UUID] = mapped_column(sa.Uuid, primary_key=True, default=uuid.uuid4)
    codigo: Mapped[str] = mapped_column(sa.String(32))
    orden: Mapped[int] = mapped_column(sa.Integer)
    inicio: Mapped[time] = mapped_column(sa.Time)
    fin: Mapped[time] = mapped_column(sa.Time)
    duracion_min: Mapped[int] = mapped_column(sa.SmallInteger)
    tipo: Mapped[TipoBloque] = mapped_column(
        enum_column(TipoBloque, nombre="ck_bloque_tipo")
    )


class AsignaturaDB(TimestampMixin, Base):
    __tablename__ = "asignatura"
    __table_args__ = (sa.UniqueConstraint("nombre", name="uq_asignatura_nombre"),)

    id: Mapped[uuid.UUID] = mapped_column(sa.Uuid, primary_key=True, default=uuid.uuid4)
    nombre: Mapped[str] = mapped_column(sa.String(120))
    color: Mapped[str] = mapped_column(sa.String(16))
    # Regla BLANDA (D-006): penaliza en el solver, nunca prohíbe.
    es_pesada: Mapped[bool] = mapped_column(
        sa.Boolean, nullable=False, default=False, server_default=sa.false()
    )


class DocenteDB(TimestampMixin, Base):
    __tablename__ = "docente"
    __table_args__ = (sa.UniqueConstraint("codigo", name="uq_docente_codigo"),)

    id: Mapped[uuid.UUID] = mapped_column(sa.Uuid, primary_key=True, default=uuid.uuid4)
    codigo: Mapped[str] = mapped_column(sa.String(32))
    nombre: Mapped[str] = mapped_column(sa.String(120))
    max_sesiones_semana: Mapped[int] = mapped_column(sa.SmallInteger)
    activo: Mapped[bool] = mapped_column(
        sa.Boolean, nullable=False, default=True, server_default=sa.true()
    )


class AptitudDB(TimestampMixin, Base):
    """Quién puede dictar qué. PK compuesta: no tiene `id` propio."""

    __tablename__ = "aptitud"

    docente_id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid, sa.ForeignKey("docente.id", ondelete="CASCADE"), primary_key=True
    )
    asignatura_id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid, sa.ForeignKey("asignatura.id", ondelete="CASCADE"), primary_key=True
    )
