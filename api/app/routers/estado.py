"""Estado global del sistema: semáforo de la barra superior y disponibilidad de IA."""

from fastapi import APIRouter
from pydantic import BaseModel

from app.ai import ai_disponible

router = APIRouter(tags=["estado"])


class EstadoResponse(BaseModel):
    ok: bool
    ai_disponible: bool


@router.get("/estado", response_model=EstadoResponse)
def leer_estado() -> EstadoResponse:
    """Sonda de salud. `ai_disponible=false` es un estado válido: todo funciona igual."""
    return EstadoResponse(ok=True, ai_disponible=ai_disponible())
