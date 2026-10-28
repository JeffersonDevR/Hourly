"""Versiones del horario y sesiones colocadas, más el overlay de escenarios."""

import uuid
from dataclasses import dataclass, field
from datetime import datetime

from app.domain.enums import EstadoVersion


@dataclass(frozen=True, slots=True)
class HorarioVersion:
    """Una versión del horario semanal.

    `escenario_id` es la única verdad del escenario activo (D-010).
    """

    numero: int
    estado: EstadoVersion
    escenario_id: uuid.UUID | None = None
    nota: str | None = None
    publicado_at: datetime | None = None
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class Sesion:
    """Una asignación colocada en (día, bloque). En el MVP ocupa un solo bloque."""

    horario_version_id: uuid.UUID
    asignacion_carga_id: uuid.UUID
    curso_id: uuid.UUID
    docente_id: uuid.UUID
    dia: int
    bloque_id: uuid.UUID
    recurso_id: uuid.UUID | None = None
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class Escenario:
    """'¿Y si...?' — no tiene columna `activo`: cuelga de la versión (D-010)."""

    nombre: str
    descripcion: str | None = None
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class EscenarioCambio:
    """Franja de un docente que cambia de disponibilidad SOLO dentro del escenario (D-005)."""

    escenario_id: uuid.UUID
    docente_id: uuid.UUID
    dia: int
    bloque_id: uuid.UUID
    disponible_nuevo: bool
    motivo: str | None = None
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    created_at: datetime | None = None
    updated_at: datetime | None = None
