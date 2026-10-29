"""Propuestas de la IA: simular, validar y recién ahí guardar (regla 3 de `AGENTS.md`).

La IA nunca escribe el horario. Sus cambios se aplican sobre una copia, se pasa `validar()`
y se descarta cualquier propuesta que **agregue** conflictos duros. Ese filtro es el que
hace que un modelo alucinando no pueda romper la demo: como mucho, no propone nada.
"""

from __future__ import annotations

import uuid
from dataclasses import replace
from typing import Any

from sqlalchemy.orm import Session

from app.ai import AIError, PropuestaIA, proveedor
from app.domain.conflictos import PropuestaCambio, PropuestaResolucion
from app.domain.enums import Gravedad, OrigenPropuesta
from app.domain.horario import Sesion
from app.repositories.conflictos import RepositorioPropuesta, RepositorioPropuestaCambio
from app.validator import EstadoHorario, validar


def _codigos(
    estado: EstadoHorario,
) -> tuple[dict[str, uuid.UUID], dict[str, uuid.UUID], dict[str, uuid.UUID]]:
    docentes = {docente.codigo: docente.id for docente in estado.docentes if docente.activo}
    bloques = {bloque.codigo: bloque.id for bloque in estado.bloques}
    recursos = {recurso.codigo: recurso.id for recurso in estado.recursos}
    return docentes, bloques, recursos


def _contexto(estado: EstadoHorario, conflicto: dict[str, Any]) -> dict[str, Any]:
    """JSON compacto: el conflicto y lo que hace falta para resolverlo, nunca el horario entero."""
    docentes, bloques, _ = _codigos(estado)
    usadas: dict[uuid.UUID, int] = {}
    for sesion in estado.sesiones:
        usadas[sesion.docente_id] = usadas.get(sesion.docente_id, 0) + 1
    afectadas = set(conflicto.get("sesion_ids", []))

    sesiones = [
        {
            "id": str(sesion.id),
            "curso": next((c.codigo for c in estado.cursos if c.id == sesion.curso_id), None),
            "docente": next(
                (d.codigo for d in estado.docentes if d.id == sesion.docente_id), None
            ),
            "dia": sesion.dia,
            "bloque": next(
                (b.codigo for b in estado.bloques if b.id == sesion.bloque_id), None
            ),
        }
        for sesion in estado.sesiones
        if str(sesion.id) in afectadas
    ]

    return {
        "docentes": [
            {
                "codigo": docente.codigo,
                "nombre": docente.nombre,
                "max_sesiones": docente.max_sesiones_semana,
                "sesiones_colocadas": usadas.get(docente.id, 0),
                "aptitudes": [
                    next(
                        (a.nombre for a in estado.asignaturas if a.id == aptitud.asignatura_id),
                        None,
                    )
                    for aptitud in estado.aptitudes
                    if aptitud.docente_id == docente.id
                ],
            }
            for docente in estado.docentes
            if docente.id in docentes.values()
        ],
        "bloques": [
            {"codigo": bloque.codigo, "orden": bloque.orden}
            for bloque in sorted(estado.bloques, key=lambda item: item.orden)
        ],
        "sesiones_afectadas": sesiones,
    }


def _aplicar(estado: EstadoHorario, propuesta: PropuestaIA) -> EstadoHorario | None:
    """Copia del estado con la propuesta aplicada, o `None` si usa un código inexistente."""
    docentes, bloques, recursos = _codigos(estado)
    cambios: dict[uuid.UUID, dict[str, Any]] = {}

    for cambio in propuesta.cambios:
        if cambio.sesion_id is None:
            return None
        destino = cambios.setdefault(cambio.sesion_id, {})
        if cambio.docente_codigo is not None:
            docente_id = docentes.get(cambio.docente_codigo)
            if docente_id is None:
                return None
            destino["docente_id"] = docente_id
        if cambio.bloque_codigo is not None:
            bloque_id = bloques.get(cambio.bloque_codigo)
            if bloque_id is None:
                return None
            destino["bloque_id"] = bloque_id
        if cambio.recurso_codigo is not None:
            recurso_id = recursos.get(cambio.recurso_codigo)
            if recurso_id is None:
                return None
            destino["recurso_id"] = recurso_id
        if cambio.dia is not None:
            if not 1 <= cambio.dia <= 5:
                return None
            destino["dia"] = cambio.dia

    conocidas = {sesion.id for sesion in estado.sesiones}
    if not set(cambios) <= conocidas:
        return None

    sesiones: tuple[Sesion, ...] = tuple(
        replace(sesion, **cambios[sesion.id]) if sesion.id in cambios else sesion
        for sesion in estado.sesiones
    )
    return replace(estado, sesiones=sesiones)


def _errores(
    estado: EstadoHorario, escenario: uuid.UUID | None
) -> set[tuple[str, tuple[uuid.UUID, ...]]]:
    return {
        (hallazgo.codigo, hallazgo.sesion_ids)
        for hallazgo in validar(estado, escenario)
        if hallazgo.gravedad is Gravedad.error
    }


def proponer_con_ia(
    sesion: Session,
    estado: EstadoHorario,
    conflicto: dict[str, Any],
    escenario_id: uuid.UUID | None,
    conflicto_id: uuid.UUID,
) -> list[PropuestaResolucion]:
    """Propuestas válidas ya persistidas. Lista vacía si la IA no está o no aporta nada."""
    try:
        crudas = proveedor().explicar_y_proponer(
            {"codigo": conflicto["codigo"], "mensaje": conflicto["mensaje"]},
            _contexto(estado, conflicto),
        )
    except AIError:
        return []

    antes = _errores(estado, escenario_id)
    repo_propuesta = RepositorioPropuesta(sesion)
    repo_cambio = RepositorioPropuestaCambio(sesion)
    guardadas: list[PropuestaResolucion] = []

    for cruda in crudas[:3]:
        simulado = _aplicar(estado, cruda)
        if simulado is None or _errores(simulado, escenario_id) - antes:
            continue
        guardada = repo_propuesta.agregar(
            PropuestaResolucion(
                origen=OrigenPropuesta.ia,
                titulo=cruda.titulo[:200],
                explicacion=cruda.explicacion,
                impacto=cruda.impacto,
                conflicto_id=conflicto_id,
            )
        )
        for cambio in cruda.cambios:
            repo_cambio.agregar(
                PropuestaCambio(
                    propuesta_id=guardada.id,
                    tipo=cambio.tipo,
                    sesion_id=cambio.sesion_id,
                    datos={
                        clave: str(valor) if isinstance(valor, uuid.UUID) else valor
                        for clave, valor in (
                            ("dia", cambio.dia),
                            ("bloque_id", _por_codigo(estado.bloques, cambio.bloque_codigo)),
                            (
                                "docente_id",
                                _por_codigo_docente(estado, cambio.docente_codigo),
                            ),
                            (
                                "recurso_id",
                                _por_codigo_recurso(estado, cambio.recurso_codigo),
                            ),
                        )
                        if valor is not None
                    },
                )
            )
        guardadas.append(guardada)

    return guardadas


def _por_codigo(bloques: tuple[Any, ...], codigo: str | None) -> uuid.UUID | None:
    if codigo is None:
        return None
    return next((bloque.id for bloque in bloques if bloque.codigo == codigo), None)


def _por_codigo_docente(estado: EstadoHorario, codigo: str | None) -> uuid.UUID | None:
    if codigo is None:
        return None
    return next((docente.id for docente in estado.docentes if docente.codigo == codigo), None)


def _por_codigo_recurso(estado: EstadoHorario, codigo: str | None) -> uuid.UUID | None:
    if codigo is None:
        return None
    return next((recurso.id for recurso in estado.recursos if recurso.codigo == codigo), None)
