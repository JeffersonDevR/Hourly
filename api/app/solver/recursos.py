"""Asignación de aulas: paso posterior al CP-SAT (ARCHITECTURE.md:10).

El modelo decide (asignación, docente, día, bloque); el aula se elige acá por
emparejamiento en la franja: mismo tipo que pide la asignación, capacidad suficiente
para el curso y libre en ese bloque. El aula titular del curso gana el desempate.

Si no hay aula válida libre, la sesión queda sin `recurso_id` y sale un diagnóstico
`RECURSO_NO_DISPONIBLE` con la causa. Nunca un `RECURSO_*` silencioso: el validador
ignora las sesiones sin recurso, así que el aviso tiene que nacer acá.
"""

import uuid
from collections.abc import Iterable

from app.domain.carga import AsignacionCarga
from app.domain.catalogo import Asignatura, Curso
from app.domain.enums import Gravedad
from app.domain.horario import Sesion
from app.domain.recursos import Recurso
from app.validator.diagnostico import Diagnostico
from app.validator.estado import EstadoHorario
from app.validator.validacion import NOMBRE_DIA

#: El aula no entra: no queda ninguna del tipo requerido con capacidad suficiente.
#: Código propio del solver: los `RECURSO_*` del validador describen un recurso
#: asignado e inválido, no la ausencia de recurso.
RECURSO_NO_DISPONIBLE = "RECURSO_NO_DISPONIBLE"

#: (día, bloque, recurso) ocupados dentro de un plan.
Ocupacion = set[tuple[int, uuid.UUID, uuid.UUID]]


def candidatos_recurso(
    estado: EstadoHorario, curso: Curso | None, asignacion: AsignacionCarga
) -> tuple[Recurso, ...]:
    """Recursos del tipo requerido que entran el curso, con el aula titular primero.

    Orden determinista: titular del curso, luego código. Sin esto el aula asignada
    dependería del orden de inserción de la DB.
    """
    estudiantes = curso.estudiantes if curso is not None else 0
    curso_id = curso.id if curso is not None else None
    validos = [
        recurso
        for recurso in estado.recursos
        if recurso.tipo_recurso == asignacion.tipo_recurso_requerido
        and recurso.capacidad >= estudiantes
    ]
    validos.sort(
        key=lambda recurso: (
            0 if curso_id is not None and recurso.curso_titular_id == curso_id else 1,
            recurso.codigo,
        )
    )
    return tuple(validos)


def elegir_recurso(
    candidatos: Iterable[Recurso],
    dia: int,
    bloque_id: uuid.UUID,
    ocupados: Ocupacion,
) -> Recurso | None:
    """Primer candidato libre en la franja. `None` si no queda ninguno."""
    for recurso in candidatos:
        if (dia, bloque_id, recurso.id) not in ocupados:
            return recurso
    return None


def asignar_recursos(
    estado: EstadoHorario, sesiones: Iterable[Sesion]
) -> tuple[tuple[Sesion, ...], tuple[Diagnostico, ...]]:
    """Completa las aulas del plan y devuelve los casos que no pudo resolver.

    Las sesiones que ya traen `recurso_id` lo conservan y reservan el aula: una
    sesión fija (D-008) no cambia de salón por regenerar. Las que vienen sin aula
    buscan la suya; si ninguna está libre en esa franja, la sesión queda sin aula
    (el validador no inventa un error que no existe) y se reporta el diagnóstico.
    """
    bloques = {bloque.id: bloque for bloque in estado.bloques}
    cursos = {curso.id: curso for curso in estado.cursos}
    asignaciones = {asignacion.id: asignacion for asignacion in estado.asignaciones}
    asignaturas = {asignatura.id: asignatura for asignatura in estado.asignaturas}

    def clave(sesion: Sesion) -> tuple:
        bloque = bloques.get(sesion.bloque_id)
        curso = cursos.get(sesion.curso_id)
        asignacion = asignaciones.get(sesion.asignacion_carga_id)
        asignatura = asignaturas.get(asignacion.asignatura_id) if asignacion else None
        return (
            sesion.dia,
            bloque.orden if bloque is not None else 0,
            curso.codigo if curso is not None else "",
            asignatura.nombre if asignatura is not None else "",
            str(sesion.asignacion_carga_id),
        )

    plan = sorted(sesiones, key=clave)
    ocupados: Ocupacion = {
        (sesion.dia, sesion.bloque_id, sesion.recurso_id)
        for sesion in plan
        if sesion.recurso_id is not None
    }

    resultado: list[Sesion] = []
    diagnosticos: list[Diagnostico] = []
    for sesion in plan:
        asignacion = asignaciones.get(sesion.asignacion_carga_id)
        if sesion.recurso_id is not None or asignacion is None:
            resultado.append(sesion)
            continue
        curso = cursos.get(sesion.curso_id)
        elegido = elegir_recurso(
            candidatos_recurso(estado, curso, asignacion),
            sesion.dia,
            sesion.bloque_id,
            ocupados,
        )
        if elegido is None:
            diagnosticos.append(_diagnostico_sin_aula(sesion, curso, asignacion, asignaturas))
            resultado.append(sesion)
            continue
        ocupados.add((sesion.dia, sesion.bloque_id, elegido.id))
        resultado.append(
            Sesion(
                horario_version_id=sesion.horario_version_id,
                asignacion_carga_id=sesion.asignacion_carga_id,
                curso_id=sesion.curso_id,
                docente_id=sesion.docente_id,
                dia=sesion.dia,
                bloque_id=sesion.bloque_id,
                recurso_id=elegido.id,
                fijada=sesion.fijada,
                id=sesion.id,
            )
        )

    return tuple(resultado), tuple(diagnosticos)


def _diagnostico_sin_aula(
    sesion: Sesion,
    curso: Curso | None,
    asignacion: AsignacionCarga,
    asignaturas: dict[uuid.UUID, Asignatura],
) -> Diagnostico:
    asignatura = asignaturas.get(asignacion.asignatura_id)
    nombre_asignatura = asignatura.nombre if asignatura is not None else "la asignatura"
    codigo_curso = curso.codigo if curso is not None else "el curso"
    estudiantes = curso.estudiantes if curso is not None else 0
    dia = NOMBRE_DIA[sesion.dia] if 0 < sesion.dia < len(NOMBRE_DIA) else f"día {sesion.dia}"
    return Diagnostico(
        codigo=RECURSO_NO_DISPONIBLE,
        gravedad=Gravedad.error,
        mensaje=(
            f"{codigo_curso} · {nombre_asignatura}: no hay "
            f"{asignacion.tipo_recurso_requerido} libre con capacidad >= {estudiantes} "
            f"el {dia}."
        ),
        asignatura=nombre_asignatura,
    )
