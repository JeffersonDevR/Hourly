"""Cassette: guarda una respuesta real por método y la replaya si el proveedor falla.

D-002 lo llama "el piso de la demo": si en el pitch se cae la red, el asistente sigue
respondiendo con la última respuesta buena grabada. Grabar requiere `AI_CASSETTE_RECORD=1`
para no ensuciar el repo al correr los tests.
"""

from __future__ import annotations

import dataclasses
import json
from pathlib import Path
from typing import Any

from app.ai.base import AIError, AIProvider, PropuestaIA, ReglaEstructurada

DIRECTORIO_CASSETTES = Path(__file__).parent / "cassettes"


def _a_json(valor: Any) -> Any:
    if dataclasses.is_dataclass(valor) and not isinstance(valor, type):
        return {
            campo.name: _a_json(getattr(valor, campo.name))
            for campo in dataclasses.fields(valor)
        }
    if isinstance(valor, tuple | list):
        return [_a_json(item) for item in valor]
    if isinstance(valor, str):
        return valor
    return valor


class CassetteProvider:
    """Envuelve un proveedor real. Si falla o no está disponible, responde del cassette."""

    def __init__(
        self,
        live: AIProvider,
        directorio: Path = DIRECTORIO_CASSETTES,
        grabar: bool = False,
    ) -> None:
        self._live = live
        self._directorio = directorio
        self._grabar = grabar

    def disponible(self) -> bool:
        return self._live.disponible() or any(self._directorio.glob("*.json"))

    def _ruta(self, nombre: str) -> Path:
        return self._directorio / f"{nombre}.json"

    def _grabar_respuesta(self, nombre: str, valor: Any) -> None:
        if not self._grabar:
            return
        self._directorio.mkdir(parents=True, exist_ok=True)
        self._ruta(nombre).write_text(
            json.dumps(_a_json(valor), ensure_ascii=False, indent=2, default=str),
            encoding="utf-8",
        )

    def _leer_cassette(self, nombre: str) -> Any:
        ruta = self._ruta(nombre)
        if not ruta.exists():
            raise AIError("El proveedor no está disponible y no hay cassette grabado.")
        return json.loads(ruta.read_text(encoding="utf-8"))

    def explicar_y_proponer(
        self, conflicto: dict[str, Any], contexto: dict[str, Any]
    ) -> list[PropuestaIA]:
        try:
            propuestas = self._live.explicar_y_proponer(conflicto, contexto)
        except AIError:
            propuestas = self._desde_cassette(self._leer_cassette("explicar_y_proponer"))
        else:
            self._grabar_respuesta("explicar_y_proponer", propuestas)
        return propuestas

    def interpretar_regla(
        self, texto: str, contexto: dict[str, Any]
    ) -> ReglaEstructurada | None:
        try:
            regla = self._live.interpretar_regla(texto, contexto)
        except AIError:
            regla = self._desde_cassette_regla(self._leer_cassette("interpretar_regla"))
        else:
            self._grabar_respuesta("interpretar_regla", regla)
        return regla

    def _desde_cassette(self, crudo: list[dict[str, Any]]) -> list[PropuestaIA]:
        from app.ai.base import CambioIA

        return [
            PropuestaIA(
                titulo=item["titulo"],
                explicacion=item["explicacion"],
                impacto=item.get("impacto"),
                cambios=tuple(
                    CambioIA(
                        tipo=cambio["tipo"],
                        sesion_id=cambio.get("sesion_id"),
                        docente_codigo=cambio.get("docente_codigo"),
                        dia=cambio.get("dia"),
                        bloque_codigo=cambio.get("bloque_codigo"),
                        recurso_codigo=cambio.get("recurso_codigo"),
                    )
                    for cambio in item["cambios"]
                ),
            )
            for item in crudo
        ]

    def _desde_cassette_regla(self, crudo: dict[str, Any] | None) -> ReglaEstructurada | None:
        if crudo is None:
            return None
        return ReglaEstructurada(
            docente_codigo=crudo["docente_codigo"],
            dias=tuple(crudo["dias"]),
            bloque_codigo=crudo.get("bloque_codigo"),
            bloquea=bool(crudo.get("bloquea", True)),
            motivo=crudo.get("motivo"),
        )
