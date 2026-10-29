"""Reglas en lenguaje natural: interpretar (parser → IA → manual) y confirmar.

`confirmar` es el único endpoint que escribe: nada se activa solo (`ARCHITECTURE.md`).
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.db import get_session
from app.services import reglas as servicio

router = APIRouter(tags=["reglas"])

Sesion = Annotated[Session, Depends(get_session)]


class InterpretarCuerpo(BaseModel):
    texto: str = Field(min_length=3, max_length=500)


class ConfirmarCuerpo(BaseModel):
    docente_codigo: str = Field(min_length=1, max_length=32)
    dias: list[int] = Field(min_length=1)
    bloque_codigo: str | None = Field(default=None, max_length=32)
    bloquea: bool = True
    motivo: str | None = Field(default=None, max_length=200)


@router.post("/reglas/interpretar")
def interpretar(datos: InterpretarCuerpo, sesion: Sesion) -> dict:
    """Frase → regla estructurada editable. `regla: null` significa "elegila a mano"."""
    return servicio.interpretar(sesion, datos.texto)


@router.post("/reglas/confirmar")
def confirmar(datos: ConfirmarCuerpo, sesion: Sesion) -> dict:
    resultado = servicio.confirmar(sesion, datos.model_dump())
    sesion.commit()
    return resultado
