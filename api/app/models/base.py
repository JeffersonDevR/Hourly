"""Base declarativa y piezas comunes de los modelos.

Decisiones de portabilidad (D-001):
- PK `sa.Uuid` con `default=uuid.uuid4` en Python, nunca `gen_random_uuid()`.
- Enums como `VARCHAR + CHECK` (`native_enum=False, create_constraint=True`).
- `sa.JSON` para todo campo `jsonb`.

Marcas de tiempo: `datetime` **naive en UTC**. SQLite no guarda zona horaria; guardar
aware haría que Postgres y SQLite devolvieran tipos distintos. `utcnow` centraliza la
regla para que no haya dos convenciones en el código.
"""

from datetime import UTC, datetime
from enum import StrEnum

import sqlalchemy as sa
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def utcnow() -> datetime:
    """Ahora, en UTC, sin tzinfo (ver docstring del módulo)."""
    return datetime.now(UTC).replace(tzinfo=None)


class Base(DeclarativeBase):
    """Base declarativa única: Alembic migra exactamente `Base.metadata`."""


class TimestampMixin:
    """`created_at`/`updated_at` en todas las tablas del esquema."""

    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime, nullable=False, default=utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        sa.DateTime, nullable=False, default=utcnow, onupdate=utcnow
    )


def enum_column(enum_clase: type[StrEnum], *, nombre: str) -> sa.Enum:
    """Columna de enum portable: VARCHAR + CHECK con nombre explícito.

    `nombre` es el nombre del CHECK (`ck_<tabla>_<columna>`), no un tipo de la DB:
    así el esquema se lee igual en SQLite que en Postgres y no hay dos enums nativos.
    """
    return sa.Enum(
        enum_clase,
        name=nombre,
        native_enum=False,
        create_constraint=True,
        validate_strings=True,
        values_callable=lambda enum: [miembro.value for miembro in enum],
    )
