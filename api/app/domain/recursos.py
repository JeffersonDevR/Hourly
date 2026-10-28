"""Recursos físicos: tipos (catálogo editable) y salones/laboratorios/canchas."""

import uuid
from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True, slots=True)
class TipoRecurso:
    """Catálogo por código: GENERAL, LAB_CIENCIAS, CANCHA, SALA_INFORMATICA.

    El código ES el nombre visible (DOMAIN.md no define otra columna).
    """

    codigo: str
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class Recurso:
    """Aula, laboratorio o cancha. `curso_titular_id` marca el aula propia del curso."""

    codigo: str
    nombre: str
    tipo_recurso: str
    capacidad: int
    curso_titular_id: uuid.UUID | None = None
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    created_at: datetime | None = None
    updated_at: datetime | None = None
