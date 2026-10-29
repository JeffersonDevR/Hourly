"""Asistente IA detrás de la interfaz `AIProvider` (D-002).

Implementaciones: `OpenAICompatibleProvider`, `NullProvider` y `CassetteProvider`.
La cadena de una sola pieza evita que la IA sea obligatoria: sin `AI_BASE_URL`,
`AI_MODEL` o `AI_API_KEY` el proveedor es `NullProvider` y todo sigue funcionando.

`interpretar_determinista` vive acá y no depende de ningún proveedor (D-004).
"""

from __future__ import annotations

import os
from typing import Any

from app.ai.base import (
    AIError,
    AIProvider,
    CambioIA,
    PropuestaIA,
    ReglaEstructurada,
)
from app.ai.cassette import CassetteProvider
from app.ai.null import NullProvider
from app.ai.openai_compatible import OpenAICompatibleProvider
from app.ai.reglas import interpretar_determinista
from app.config import get_settings

_proveedor: AIProvider | None = None
_inyectado: AIProvider | None = None


def proveedor() -> AIProvider:
    """Proveedor vigente. Cacheado: construir el cliente en cada request es caro."""
    global _proveedor
    if _inyectado is not None:
        return _inyectado
    if _proveedor is None:
        settings = get_settings()
        if not (settings.ai_base_url and settings.ai_model and settings.ai_api_key):
            _proveedor = NullProvider()
        else:
            live = OpenAICompatibleProvider(
                base_url=settings.ai_base_url,
                model=settings.ai_model,
                api_key=settings.ai_api_key,
                timeout_s=settings.solver_timeout_s,
            )
            _proveedor = CassetteProvider(
                live, grabar=os.getenv("AI_CASSETTE_RECORD") == "1"
            )
    return _proveedor


def ai_disponible() -> bool:
    try:
        return proveedor().disponible()
    except Exception:  # un proveedor mal configurado no puede tumbar `/api/estado`
        return False


def establecer_proveedor(nuevo: AIProvider | None) -> None:
    """Inyecta un proveedor (tests, o un stub del pitch). `None` restaura el de entorno."""
    global _inyectado, _proveedor
    _inyectado = nuevo
    _proveedor = None


__all__ = [
    "AIError",
    "AIProvider",
    "CambioIA",
    "CassetteProvider",
    "NullProvider",
    "OpenAICompatibleProvider",
    "PropuestaIA",
    "ReglaEstructurada",
    "ai_disponible",
    "establecer_proveedor",
    "interpretar_determinista",
    "proveedor",
]

# `Any` se usa en la firma de `AIProvider`; se deja importado para los stubs de test.
_ = Any
