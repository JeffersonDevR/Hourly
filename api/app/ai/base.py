"""Contrato del asistente (D-002).

El proveedor es opcional y siempre externo al solver: si falla, no hay API key o expira,
todo el producto sigue funcionando con `NullProvider` y la UI dice "Asistente IA no
disponible". Nada de lo que devuelve se aplica sin simularlo y validarlo (regla 3 de
`AGENTS.md`).
"""

import uuid
from dataclasses import dataclass
from typing import Any, Protocol

from app.domain.enums import TipoCambioPropuesta


class AIError(RuntimeError):
    """Falla del proveedor: red, timeout, JSON inválido o respuesta fuera de contrato."""


@dataclass(frozen=True, slots=True)
class CambioIA:
    """Un cambio propuesto por la IA. Usa CÓDIGOS, no ids: el modelo solo repite lo que vio.

    La resolución código → id la hace la API contra el catálogo, que es la única fuente
    de verdad; un id inventado por el modelo no puede llegar a la DB.
    """

    tipo: TipoCambioPropuesta
    sesion_id: uuid.UUID | None = None
    docente_codigo: str | None = None
    dia: int | None = None
    bloque_codigo: str | None = None
    recurso_codigo: str | None = None


@dataclass(frozen=True, slots=True)
class PropuestaIA:
    titulo: str
    explicacion: str
    impacto: str | None
    cambios: tuple[CambioIA, ...]


@dataclass(frozen=True, slots=True)
class ReglaEstructurada:
    """Regla en lenguaje natural ya estructurada. `bloque_codigo=None` = todo el día."""

    docente_codigo: str
    dias: tuple[int, ...]
    bloque_codigo: str | None = None
    bloquea: bool = True
    motivo: str | None = None


class AIProvider(Protocol):
    """Las tres operaciones del contrato (`ARCHITECTURE.md`)."""

    def disponible(self) -> bool: ...

    def explicar_y_proponer(
        self, conflicto: dict[str, Any], contexto: dict[str, Any]
    ) -> list[PropuestaIA]: ...

    def interpretar_regla(
        self, texto: str, contexto: dict[str, Any]
    ) -> ReglaEstructurada | None: ...
