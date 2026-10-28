"""Conflictos detectados por el validador y propuestas de resolución (solver o IA)."""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from app.domain.enums import (
    EstadoConflicto,
    EstadoPropuesta,
    Gravedad,
    OrigenPropuesta,
    TipoCambioPropuesta,
)


@dataclass(frozen=True, slots=True)
class Conflicto:
    """Una violación detectada sobre una versión concreta. `codigo` es el del validador."""

    horario_version_id: uuid.UUID
    codigo: str
    gravedad: Gravedad
    mensaje: str
    estado: EstadoConflicto = EstadoConflicto.abierto
    detalle: dict[str, Any] | None = None
    detectado_at: datetime | None = None
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class ConflictoSesion:
    """Sesiones afectadas por un conflicto. PK compuesta: borrar cualquiera de las dos
    entidades elimina el vínculo."""

    conflicto_id: uuid.UUID
    sesion_id: uuid.UUID
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class PropuestaResolucion:
    """Propuesta de arreglo para un conflicto (D-003: solver primero, IA después)."""

    origen: OrigenPropuesta
    titulo: str
    explicacion: str
    impacto: str | None = None
    conflicto_id: uuid.UUID | None = None
    estado: EstadoPropuesta = EstadoPropuesta.pendiente
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class PropuestaCambio:
    """Un cambio concreto dentro de una propuesta. `datos` guarda los valores nuevos."""

    propuesta_id: uuid.UUID
    tipo: TipoCambioPropuesta
    datos: dict[str, Any]
    sesion_id: uuid.UUID | None = None
    asignacion_carga_id: uuid.UUID | None = None
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    created_at: datetime | None = None
    updated_at: datetime | None = None
