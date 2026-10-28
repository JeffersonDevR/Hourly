"""Estado global del sistema: semáforo de la barra superior y disponibilidad de IA."""

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(tags=["estado"])


class EstadoResponse(BaseModel):
    ok: bool
    ai_disponible: bool


@router.get("/estado", response_model=EstadoResponse)
def leer_estado() -> EstadoResponse:
    """Sonda de salud de la API.

    `ai_disponible` queda en `False` hasta que exista el proveedor de IA
    (fase 8, D-002). La app es 100% funcional en ese estado.
    """
    return EstadoResponse(ok=True, ai_disponible=False)
