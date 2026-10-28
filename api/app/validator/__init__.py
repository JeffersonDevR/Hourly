"""Validador único: `validar(estado, escenario=None, al_publicar=False)` y
`diagnosticar_carga(estado)`.

Función pura sobre dataclasses, sin DB ni IA (`AGENTS.md`, regla 1). La API, el
solver, la importación y las propuestas de la IA consumen este paquete.
"""

from app.validator.conflictos import (
    ASIGNATURA_PESADA_CONSECUTIVA,
    BLOQUE_NO_CLASE,
    CURSO_DOBLE,
    DOCENTE_DOBLE,
    DOCENTE_NO_DISPONIBLE,
    DOCENTE_NO_HABILITADO,
    DOCENTE_SOBRECARGA,
    MALLA_INCUMPLIDA,
    RECURSO_CAPACIDAD,
    RECURSO_DOBLE,
    RECURSO_TIPO_INCORRECTO,
    Conflicto,
)
from app.validator.diagnostico import (
    ASIGNATURA_UNICO_DOCENTE,
    DOCENTE_SIN_HOLGURA,
    Diagnostico,
    diagnosticar_carga,
)
from app.validator.estado import EstadoHorario
from app.validator.validacion import validar

__all__ = [
    "ASIGNATURA_PESADA_CONSECUTIVA",
    "ASIGNATURA_UNICO_DOCENTE",
    "BLOQUE_NO_CLASE",
    "CURSO_DOBLE",
    "DOCENTE_DOBLE",
    "DOCENTE_NO_DISPONIBLE",
    "DOCENTE_NO_HABILITADO",
    "DOCENTE_SIN_HOLGURA",
    "DOCENTE_SOBRECARGA",
    "MALLA_INCUMPLIDA",
    "RECURSO_CAPACIDAD",
    "RECURSO_DOBLE",
    "RECURSO_TIPO_INCORRECTO",
    "Conflicto",
    "Diagnostico",
    "EstadoHorario",
    "diagnosticar_carga",
    "validar",
]
