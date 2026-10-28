"""Conflictos que devuelve el validador: código, gravedad, mensaje y sesiones.

`Conflicto` es el resultado puro de `validar()`. No lleva `horario_version_id` ni
`id` porque el validador no conoce la DB: quien persiste (fase 5) lo mapea a
`app.domain.conflictos.Conflicto` + `ConflictoSesion` y decide la versión. Los
códigos son los de la tabla de invariantes de `DOMAIN.md`.
"""

import uuid
from dataclasses import dataclass

from app.domain.enums import Gravedad

#: Docente, curso o recurso en dos sesiones de la misma (versión, día, bloque).
DOCENTE_DOBLE = "DOCENTE_DOBLE"
CURSO_DOBLE = "CURSO_DOBLE"
RECURSO_DOBLE = "RECURSO_DOBLE"
#: Sesión colocada en un bloque que no es de clase.
BLOQUE_NO_CLASE = "BLOQUE_NO_CLASE"
#: Sesión en una franja bloqueada del docente (con el escenario ya aplicado).
DOCENTE_NO_DISPONIBLE = "DOCENTE_NO_DISPONIBLE"
#: Docente sin `aptitud` para la asignatura de la sesión.
DOCENTE_NO_HABILITADO = "DOCENTE_NO_HABILITADO"
#: El recurso asignado no es del tipo que pide la asignación.
RECURSO_TIPO_INCORRECTO = "RECURSO_TIPO_INCORRECTO"
#: Capacidad del recurso menor que los estudiantes del curso.
RECURSO_CAPACIDAD = "RECURSO_CAPACIDAD"
#: Sesiones colocadas del docente por encima de `max_sesiones_semana`.
DOCENTE_SOBRECARGA = "DOCENTE_SOBRECARGA"
#: Sesiones colocadas distintas de `sesiones_semana` (gravedad según `al_publicar`).
MALLA_INCUMPLIDA = "MALLA_INCUMPLIDA"
#: Dos bloques de clase consecutivos con asignaturas pesadas (regla blanda, D-006).
ASIGNATURA_PESADA_CONSECUTIVA = "ASIGNATURA_PESADA_CONSECUTIVA"


@dataclass(frozen=True, slots=True)
class Conflicto:
    """Un hallazgo del validador. `sesion_ids` son las sesiones afectadas.

    `gravedad` se decide en cada evaluación, no se persiste como verdad aparte
    (D-011): `MALLA_INCUMPLIDA` cambia entre advertencia y error según `al_publicar`.
    """

    codigo: str
    gravedad: Gravedad
    mensaje: str
    sesion_ids: tuple[uuid.UUID, ...] = ()
