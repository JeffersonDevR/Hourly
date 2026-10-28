"""Catálogos base: institución, grados, cursos, bloques, asignaturas y docentes.

Dataclasses inmutables (`frozen=True`), sin SQLAlchemy ni FastAPI. El `id` y las
marcas de tiempo tienen default para poder construir entidades en memoria
(validador, solver, tests) sin pasar por la DB.
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, time

from app.domain.enums import TipoBloque


@dataclass(frozen=True, slots=True)
class Institucion:
    """Una sola fila en Fase 1."""

    nombre: str
    logo_url: str | None = None
    color_acento: str | None = None
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class Grado:
    """Grado escolar configurable (el Excel usa 6 y 7)."""

    nombre: str
    orden: int
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class Curso:
    """Grupo de estudiantes al que se le arma el horario ('6A', '7B')."""

    codigo: str
    nombre: str
    grado_id: uuid.UUID
    estudiantes: int
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class Bloque:
    """Franja horaria del día. `orden` define la secuencia dentro del día."""

    codigo: str
    orden: int
    inicio: time
    fin: time
    duracion_min: int
    tipo: TipoBloque
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class Asignatura:
    """Materia. `es_pesada` alimenta la regla blanda D-006, nunca una restricción dura."""

    nombre: str
    color: str
    es_pesada: bool = False
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class Docente:
    """Docente. `max_sesiones_semana` se cuenta en sesiones (bloques), no en horas."""

    codigo: str
    nombre: str
    max_sesiones_semana: int
    activo: bool = True
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class Aptitud:
    """Quién puede dictar qué. La PK es la pareja (docente, asignatura)."""

    docente_id: uuid.UUID
    asignatura_id: uuid.UUID
    created_at: datetime | None = None
    updated_at: datetime | None = None
