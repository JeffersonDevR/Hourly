"""Proveedor contra cualquier API compatible con OpenAI (`/v1/chat/completions`).

D-002: el SDK `openai` es solo el transporte. La salida se valida con Pydantic y nunca se
usa `response_format` con JSON schema (no es portable entre proveedores). Un error, un
timeout o un JSON inválido se convierten en `AIError` y el llamador cae a `NullProvider`.
"""

from __future__ import annotations

import json
import re
import uuid
from pathlib import Path
from typing import Any

from openai import OpenAI
from pydantic import BaseModel, ValidationError

from app.ai.base import AIError, CambioIA, PropuestaIA, ReglaEstructurada
from app.domain.enums import TipoCambioPropuesta

TIMEOUT_S = 20.0

PROMPTS = Path(__file__).parent / "prompts"


def _prompt(nombre: str) -> str:
    return (PROMPTS / f"{nombre}.md").read_text(encoding="utf-8")


class _CambioCrudo(BaseModel):
    tipo: TipoCambioPropuesta
    sesion_id: str | None = None
    docente_codigo: str | None = None
    dia: int | None = None
    bloque_codigo: str | None = None
    recurso_codigo: str | None = None


class _PropuestaCruda(BaseModel):
    titulo: str
    explicacion_simple: str
    impacto: str | None = None
    cambios: list[_CambioCrudo]


class _RespuestaPropuestas(BaseModel):
    propuestas: list[_PropuestaCruda]


class _ReglaCruda(BaseModel):
    docente_codigo: str
    dias: list[int]
    bloque_codigo: str | None = None
    bloquea: bool = True
    motivo: str | None = None


class _RespuestaRegla(BaseModel):
    regla: _ReglaCruda | None


def _json(texto: str) -> Any:
    """Extrae el JSON aunque el modelo lo envuelva en ```json … ```."""
    limpio = texto.strip()
    cerco = re.search(r"```(?:json)?\s*(.+?)```", limpio, re.S)
    if cerco:
        limpio = cerco.group(1).strip()
    desde = limpio.find("{")
    hasta = limpio.rfind("}")
    if desde == -1 or hasta == -1:
        raise AIError("La respuesta no contiene JSON.")
    try:
        return json.loads(limpio[desde : hasta + 1])
    except json.JSONDecodeError as exc:
        raise AIError(f"JSON inválido: {exc}") from exc


class OpenAICompatibleProvider:
    def __init__(self, base_url: str, model: str, api_key: str, timeout_s: float = TIMEOUT_S):
        self._model = model
        self._cliente = OpenAI(
            base_url=base_url, api_key=api_key, timeout=timeout_s, max_retries=1
        )

    def disponible(self) -> bool:
        return True

    def _completar(self, sistema: str, usuario: str) -> Any:
        try:
            respuesta = self._cliente.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": sistema},
                    {"role": "user", "content": usuario},
                ],
                temperature=0,
            )
            texto = respuesta.choices[0].message.content or ""
        except Exception as exc:  # red, timeout, 429, 5xx: todo es "IA no disponible"
            raise AIError(str(exc)) from exc
        return _json(texto)

    def explicar_y_proponer(
        self, conflicto: dict[str, Any], contexto: dict[str, Any]
    ) -> list[PropuestaIA]:
        crudo = self._completar(
            _prompt("propuestas"),
            json.dumps({"conflicto": conflicto, "contexto": contexto}, ensure_ascii=False),
        )
        try:
            respuesta = _RespuestaPropuestas.model_validate(crudo)
        except ValidationError as exc:
            raise AIError(f"Propuestas fuera de contrato: {exc}") from exc
        return [
            PropuestaIA(
                titulo=propuesta.titulo,
                explicacion=propuesta.explicacion_simple,
                impacto=propuesta.impacto,
                cambios=tuple(
                    CambioIA(
                        tipo=cambio.tipo,
                        sesion_id=_uuid(cambio.sesion_id),
                        docente_codigo=cambio.docente_codigo,
                        dia=cambio.dia,
                        bloque_codigo=cambio.bloque_codigo,
                        recurso_codigo=cambio.recurso_codigo,
                    )
                    for cambio in propuesta.cambios
                ),
            )
            for propuesta in respuesta.propuestas
        ]

    def interpretar_regla(
        self, texto: str, contexto: dict[str, Any]
    ) -> ReglaEstructurada | None:
        crudo = self._completar(
            _prompt("regla"),
            json.dumps({"texto": texto, "contexto": contexto}, ensure_ascii=False),
        )
        try:
            respuesta = _RespuestaRegla.model_validate(crudo)
        except ValidationError as exc:
            raise AIError(f"Regla fuera de contrato: {exc}") from exc
        if respuesta.regla is None:
            return None
        regla = respuesta.regla
        return ReglaEstructurada(
            docente_codigo=regla.docente_codigo,
            dias=tuple(sorted({dia for dia in regla.dias if 1 <= dia <= 5})),
            bloque_codigo=regla.bloque_codigo,
            bloquea=regla.bloquea,
            motivo=regla.motivo,
        )


def _uuid(valor: str | None) -> uuid.UUID | None:
    if not valor:
        return None
    try:
        return uuid.UUID(valor)
    except ValueError:
        return None
