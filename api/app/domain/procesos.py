"""Procesos de larga duración y trazas: ejecuciones del solver, importaciones e historial."""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from app.domain.enums import Gravedad, ModoDocente


@dataclass(frozen=True, slots=True)
class EjecucionSolver:
    """Corrida de CP-SAT. `diagnostico` se llena cuando el resultado es INFACTIBLE."""

    modo_docente: ModoDocente
    estado: str
    horario_version_id: uuid.UUID | None = None
    diagnostico: dict[str, Any] | None = None
    iniciado_at: datetime | None = None
    terminado_at: datetime | None = None
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class Importacion:
    """Carga de un Excel. `resumen` guarda los conteos del preview."""

    archivo_nombre: str
    estado: str
    resumen: dict[str, Any] | None = None
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class ImportacionError:
    """Hallazgo por celda de una importación, corregible antes de confirmar."""

    importacion_id: uuid.UUID
    severidad: Gravedad
    mensaje: str
    hoja: str | None = None
    fila: int | None = None
    columna: str | None = None
    codigo: str | None = None
    corregido: bool = False
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class HistorialCambio:
    """Entrada de deshacer/rehacer. La escribe SOLO `app.services.historial`."""

    entidad: str
    entidad_id: str
    accion: str
    antes: dict[str, Any] | None = None
    despues: dict[str, Any] | None = None
    horario_version_id: uuid.UUID | None = None
    ocurrido_at: datetime | None = None
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    created_at: datetime | None = None
    updated_at: datetime | None = None
