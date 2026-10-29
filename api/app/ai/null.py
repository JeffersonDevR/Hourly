"""Proveedor nulo: sin red, sin key, sin sorpresas.

Es el piso del producto (golden 5): con `NullProvider` los flujos de importación,
validación, solver y publicación funcionan y `/api/estado.ai_disponible` es `false`.
"""

from typing import Any

from app.ai.base import PropuestaIA, ReglaEstructurada


class NullProvider:
    def disponible(self) -> bool:
        return False

    def explicar_y_proponer(
        self, conflicto: dict[str, Any], contexto: dict[str, Any]
    ) -> list[PropuestaIA]:
        return []

    def interpretar_regla(
        self, texto: str, contexto: dict[str, Any]
    ) -> ReglaEstructurada | None:
        return None
