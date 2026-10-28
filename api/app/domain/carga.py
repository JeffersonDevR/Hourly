"""Carga académica y disponibilidad base del docente."""

import uuid
from dataclasses import dataclass, field
from datetime import datetime

from app.domain.enums import OrigenBloqueo


@dataclass(frozen=True, slots=True)
class AsignacionCarga:
    """Cuántas sesiones semanales de una asignatura necesita un curso, y con quién."""

    curso_id: uuid.UUID
    asignatura_id: uuid.UUID
    docente_principal_id: uuid.UUID
    sesiones_semana: int
    tipo_recurso_requerido: str
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class DisponibilidadBloqueo:
    """Franja en la que el docente NO está disponible. Estado base, no escenario (D-005)."""

    docente_id: uuid.UUID
    dia: int
    bloque_id: uuid.UUID
    origen: OrigenBloqueo
    detalle: str | None = None
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    created_at: datetime | None = None
    updated_at: datetime | None = None
