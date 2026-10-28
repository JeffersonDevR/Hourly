"""Resultado del solver: estado final, sesiones y diagnóstico legible.

`Resultado` es lo que sale de `resolver(...)` (ARCHITECTURE.md:6). El calor del
CP-SAT queda en `objetivo`, que es determinista y sirve para comparar corridas
(por ejemplo, medir el efecto de la penalidad de materias pesadas).
"""

from dataclasses import dataclass
from enum import StrEnum

from app.domain.horario import Sesion
from app.validator.diagnostico import Diagnostico


class EstadoResultado(StrEnum):
    """Cómo terminó la corrida. Los cuatro valores del contrato de la fase 4."""

    OPTIMO = "OPTIMO"
    FACTIBLE = "FACTIBLE"
    INFACTIBLE = "INFACTIBLE"
    TIMEOUT = "TIMEOUT"


@dataclass(frozen=True, slots=True)
class Resultado:
    """Plan completo (fijas + generadas) o la causa de que no exista.

    Attributes:
        estado: `OPTIMO` si CP-SAT demostró optimalidad, `FACTIBLE` si encontró una
            solución sin demostrarla, `INFACTIBLE` si no existe, `TIMEOUT` si se
            agotó `SOLVER_TIMEOUT_S` sin demostrar nada. En `TIMEOUT` con solución
            incumbente se devuelven esas sesiones: son válidas, solo no óptimas.
        sesiones: sesiones del plan con su aula asignada, ordenadas por
            (día, bloque, curso, asignatura). Vacía si no hay solución.
        diagnostico: aritmética de `diagnosticar_carga` cuando no hay solución, más
            los casos de recurso que el post-paso no pudo resolver. Nunca una lista
            de errores `RECURSO_*` silenciosa.
        objetivo: valor de la función objetivo de CP-SAT. `None` si no hubo solución.
    """

    estado: EstadoResultado
    sesiones: tuple[Sesion, ...] = ()
    diagnostico: tuple[Diagnostico, ...] = ()
    objetivo: int | None = None


__all__ = ["EstadoResultado", "Resultado"]
