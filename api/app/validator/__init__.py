"""Validador único: `validar(estado, escenario=None)` y `diagnosticar_carga(estado)`.

Función pura sobre dataclasses, sin DB ni IA (`AGENTS.md`, regla 1). En fase 2 existe
`diagnosticar_carga`; `validar()` se agrega en fase 3 sobre el mismo `EstadoHorario`.
"""

from app.validator.diagnostico import (
    ASIGNATURA_UNICO_DOCENTE,
    DOCENTE_SIN_HOLGURA,
    DOCENTE_SOBRECARGA,
    Diagnostico,
    diagnosticar_carga,
)
from app.validator.estado import EstadoHorario

__all__ = [
    "ASIGNATURA_UNICO_DOCENTE",
    "DOCENTE_SIN_HOLGURA",
    "DOCENTE_SOBRECARGA",
    "Diagnostico",
    "EstadoHorario",
    "diagnosticar_carga",
]
