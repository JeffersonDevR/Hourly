"""Paso 0 de D-003: reparación local greedy. Determinista, sin DB y sin IA.

Tres movimientos, en ese vocabulario y no en otro (`propuesta_cambio.tipo`):

- `mover_sesion`: la sesión cambia de franja dentro del horario;
- `cambiar_docente`: pasa a otro docente con `aptitud` y capacidad semanal;
- `cambiar_recurso`: pasa a otro recurso del tipo requerido y con capacidad.

Devuelve PROPUESTAS: nunca muta `EstadoHorario` ni la lista de sesiones del llamador.
El llamador decide si las aplica (fase 5) y `validar()` da la última palabra.

Por qué existe: D-003 resuelve primero con código determinista y deja la IA para lo
que el código no previó. El greedy es ciego en instancias sin holgura —D1 y D3 están
en 24/24— y por eso CP-SAT sigue siendo obligatorio después. Acá no se reemplaza.
"""

import uuid
from collections.abc import Iterable
from dataclasses import dataclass, replace

from app.domain.enums import Gravedad, TipoCambioPropuesta
from app.domain.horario import Sesion
from app.solver.comun import (
    DIAS,
    bloques_clase,
    carga_por_docente,
    franjas_bloqueadas,
)
from app.solver.recursos import candidatos_recurso, elegir_recurso
from app.validator import (
    BLOQUE_NO_CLASE,
    CURSO_DOBLE,
    DOCENTE_DOBLE,
    DOCENTE_NO_DISPONIBLE,
    DOCENTE_NO_HABILITADO,
    DOCENTE_SOBRECARGA,
    RECURSO_CAPACIDAD,
    RECURSO_DOBLE,
    RECURSO_TIPO_INCORRECTO,
    validar,
)
from app.validator.estado import EstadoHorario

#: Qué intentar por cada código de conflicto, en orden. `mover` primero conserva el
#: docente cuando se puede; en los conflictos de disponibilidad el docente es el que
#: está mal, así que se cambia primero.
ESTRATEGIAS: dict[str, tuple[str, ...]] = {
    DOCENTE_DOBLE: ("mover", "docente"),
    DOCENTE_NO_DISPONIBLE: ("docente", "mover"),
    DOCENTE_NO_HABILITADO: ("docente",),
    DOCENTE_SOBRECARGA: ("docente",),
    CURSO_DOBLE: ("mover",),
    RECURSO_DOBLE: ("recurso", "mover"),
    RECURSO_TIPO_INCORRECTO: ("recurso",),
    RECURSO_CAPACIDAD: ("recurso",),
    BLOQUE_NO_CLASE: ("mover",),
}


@dataclass(frozen=True, slots=True)
class PropuestaCambio:
    """Un cambio concreto sobre una sesión. Lo que fase 5 escribe en `propuesta_cambio`.

    Solo se llenan los campos del tipo: `mover_sesion` usa `dia` y `bloque_id`,
    `cambiar_docente` usa `docente_id`, `cambiar_recurso` usa `recurso_id`.
    """

    tipo: TipoCambioPropuesta
    sesion_id: uuid.UUID
    dia: int | None = None
    bloque_id: uuid.UUID | None = None
    docente_id: uuid.UUID | None = None
    recurso_id: uuid.UUID | None = None


def reparar_greedy(
    estado: EstadoHorario,
    escenario: object = None,
    fijas: Iterable[Sesion] = (),
    limite: int | None = None,
) -> tuple[PropuestaCambio, ...]:
    """Propuestas deterministas que resuelven conflictos duros, sin aplicarlas.

    Args:
        estado: foto del horario.
        escenario: objeto o id del escenario activo (overlay D-005).
        fijas: sesiones que no se pueden tocar (D-008). Acepta sesiones o ids.
        limite: tope de propuestas. `None` = una por conflicto como máximo.

    Returns:
        Propuestas en orden determinista, ya simuladas sobre una copia interna: dos
        propuestas nunca se pisan. Vacía si ningún movimiento es válido.
    """
    trabajo = list(estado.sesiones)
    inmoviles = {_sesion_id(elemento) for elemento in fijas}
    bloqueadas = franjas_bloqueadas(estado, escenario)
    orden = _orden(estado)

    conflictos = [
        conflicto
        for conflicto in validar(estado, escenario)
        if conflicto.gravedad == Gravedad.error
    ]
    propuestas: list[PropuestaCambio] = []
    tocadas: set[uuid.UUID] = set()

    for conflicto in conflictos:
        if limite is not None and len(propuestas) >= limite:
            break
        afectadas = set(conflicto.sesion_ids)
        candidatas = [
            sesion
            for sesion in trabajo
            if sesion.id in afectadas and sesion.id not in inmoviles and sesion.id not in tocadas
        ]
        # La última colocada primero: en un choque, la que llegó después es la que
        # se mueve. El orden sale de los códigos del dominio (curso, asignatura), no
        # de los UUID, que son aleatorios en la DB y romperían el determinismo.
        candidatas.sort(key=orden, reverse=True)
        for sesion in candidatas:
            propuesta = _intentar(conflicto.codigo, sesion, trabajo, estado, bloqueadas)
            if propuesta is None:
                continue
            propuestas.append(propuesta)
            tocadas.add(sesion.id)
            trabajo = _aplicar(trabajo, propuesta)
            break

    return tuple(propuestas)


def _sesion_id(elemento: Sesion | uuid.UUID) -> uuid.UUID:
    return elemento if isinstance(elemento, uuid.UUID) else elemento.id


def _orden(estado: EstadoHorario):
    """Clave de orden por datos del dominio: día, bloque, curso, asignatura."""
    bloques = {bloque.id: bloque.orden for bloque in estado.bloques}
    cursos = {curso.id: curso.codigo for curso in estado.cursos}
    asignaciones = {asignacion.id: asignacion for asignacion in estado.asignaciones}
    asignaturas = {asignatura.id: asignatura.nombre for asignatura in estado.asignaturas}

    def clave(sesion: Sesion) -> tuple:
        asignacion = asignaciones.get(sesion.asignacion_carga_id)
        return (
            sesion.dia,
            bloques.get(sesion.bloque_id, 0),
            cursos.get(sesion.curso_id, ""),
            asignaturas.get(asignacion.asignatura_id, "") if asignacion is not None else "",
        )

    return clave


def _intentar(
    codigo: str,
    sesion: Sesion,
    trabajo: list[Sesion],
    estado: EstadoHorario,
    bloqueadas: set[tuple[uuid.UUID, int, uuid.UUID]],
) -> PropuestaCambio | None:
    for estrategia in ESTRATEGIAS.get(codigo, ()):
        if estrategia == "mover":
            propuesta = _mover(sesion, trabajo, estado, bloqueadas)
        elif estrategia == "docente":
            propuesta = _cambiar_docente(sesion, trabajo, estado, bloqueadas)
        else:
            propuesta = _cambiar_recurso(sesion, trabajo, estado)
        if propuesta is not None:
            return propuesta
    return None


def _mover(
    sesion: Sesion,
    trabajo: list[Sesion],
    estado: EstadoHorario,
    bloqueadas: set[tuple[uuid.UUID, int, uuid.UUID]],
) -> PropuestaCambio | None:
    """Primera franja de clase libre y válida, barriendo desde la actual."""
    bloques = bloques_clase(estado)
    if not bloques:
        return None
    posiciones = [(dia, bloque) for dia in DIAS for bloque in bloques]
    actual = next(
        (
            indice
            for indice, (dia, bloque) in enumerate(posiciones)
            if dia == sesion.dia and bloque.id == sesion.bloque_id
        ),
        None,
    )
    # Rotar desde la posición actual: sin esto todas las reparaciones caen en el
    # lunes a primera hora y el horario queda peor que antes del greedy.
    orden = posiciones[actual + 1 :] + posiciones if actual is not None else posiciones
    for dia, bloque in orden:
        if dia == sesion.dia and bloque.id == sesion.bloque_id:
            continue
        if _franja_libre(sesion, dia, bloque.id, trabajo, bloqueadas):
            return PropuestaCambio(
                tipo=TipoCambioPropuesta.mover_sesion,
                sesion_id=sesion.id,
                dia=dia,
                bloque_id=bloque.id,
            )
    return None


def _franja_libre(
    sesion: Sesion,
    dia: int,
    bloque_id: uuid.UUID,
    trabajo: list[Sesion],
    bloqueadas: set[tuple[uuid.UUID, int, uuid.UUID]],
) -> bool:
    """Mismas reglas duras que `validar()`, aplicadas a un movimiento concreto."""
    if (sesion.docente_id, dia, bloque_id) in bloqueadas:
        return False
    for otra in trabajo:
        if otra.id == sesion.id or otra.dia != dia or otra.bloque_id != bloque_id:
            continue
        if otra.curso_id == sesion.curso_id:
            return False
        if otra.docente_id == sesion.docente_id:
            return False
        if sesion.recurso_id is not None and otra.recurso_id == sesion.recurso_id:
            return False
    return True


def _cambiar_docente(
    sesion: Sesion,
    trabajo: list[Sesion],
    estado: EstadoHorario,
    bloqueadas: set[tuple[uuid.UUID, int, uuid.UUID]],
) -> PropuestaCambio | None:
    """Otro docente con `aptitud`, activo, con capacidad y libre en esa franja."""
    asignacion = _asignacion(sesion, estado)
    if asignacion is None:
        return None
    docentes = {docente.id: docente for docente in estado.docentes if docente.activo}
    aptos = {
        aptitud.docente_id
        for aptitud in estado.aptitudes
        if aptitud.asignatura_id == asignacion.asignatura_id
    }
    carga = carga_por_docente(trabajo)
    candidatos = [
        docentes[docente_id]
        for docente_id in aptos
        if docente_id in docentes
        and docente_id != sesion.docente_id
        and carga.get(docente_id, 0) < docentes[docente_id].max_sesiones_semana
    ]
    candidatos.sort(key=lambda docente: (carga.get(docente.id, 0), docente.codigo))

    for docente in candidatos:
        if (docente.id, sesion.dia, sesion.bloque_id) in bloqueadas:
            continue
        ocupado = any(
            otra.id != sesion.id
            and otra.dia == sesion.dia
            and otra.bloque_id == sesion.bloque_id
            and otra.docente_id == docente.id
            for otra in trabajo
        )
        if ocupado:
            continue
        return PropuestaCambio(
            tipo=TipoCambioPropuesta.cambiar_docente,
            sesion_id=sesion.id,
            docente_id=docente.id,
        )
    return None


def _cambiar_recurso(
    sesion: Sesion, trabajo: list[Sesion], estado: EstadoHorario
) -> PropuestaCambio | None:
    """Otro recurso del tipo y capacidad requeridos, libre en la franja."""
    asignacion = _asignacion(sesion, estado)
    if asignacion is None:
        return None
    curso = next((curso for curso in estado.cursos if curso.id == sesion.curso_id), None)
    ocupados = {
        (otra.dia, otra.bloque_id, otra.recurso_id)
        for otra in trabajo
        if otra.id != sesion.id and otra.recurso_id is not None
    }
    elegido = elegir_recurso(
        candidatos_recurso(estado, curso, asignacion),
        sesion.dia,
        sesion.bloque_id,
        ocupados,
    )
    if elegido is None or elegido.id == sesion.recurso_id:
        return None
    return PropuestaCambio(
        tipo=TipoCambioPropuesta.cambiar_recurso,
        sesion_id=sesion.id,
        recurso_id=elegido.id,
    )


def _asignacion(sesion: Sesion, estado: EstadoHorario):
    return next(
        (
            asignacion
            for asignacion in estado.asignaciones
            if asignacion.id == sesion.asignacion_carga_id
        ),
        None,
    )


def _aplicar(trabajo: list[Sesion], propuesta: PropuestaCambio) -> list[Sesion]:
    """Copia del plan con la propuesta ya simulada (el estado del llamador no cambia)."""
    cambios = {
        clave: valor
        for clave, valor in (
            ("dia", propuesta.dia),
            ("bloque_id", propuesta.bloque_id),
            ("docente_id", propuesta.docente_id),
            ("recurso_id", propuesta.recurso_id),
        )
        if valor is not None
    }
    return [
        replace(sesion, **cambios) if sesion.id == propuesta.sesion_id else sesion
        for sesion in trabajo
    ]


__all__ = ["ESTRATEGIAS", "PropuestaCambio", "reparar_greedy"]
