"""API de versiones, sesiones, conflictos, propuestas y publicación.

Traduce HTTP <-> `app.services.horario`. El solver corre en un hilo aparte
(`run_in_threadpool`, D-007): CP-SAT bloquea y en un endpoint `async` congelaría toda
la API, no solo el spinner.
"""

from __future__ import annotations

import uuid
from dataclasses import asdict, replace
from functools import partial
from typing import Annotated, Any

import sqlalchemy as sa
from fastapi import APIRouter, Depends, Query, Response
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from app.db import get_session
from app.domain.enums import EstadoVersion, Gravedad
from app.domain.horario import Escenario, HorarioVersion, Sesion
from app.domain.procesos import EjecucionSolver
from app.exporter.excel import MEDIA_TYPE_XLSX, exportar_xlsx
from app.exporter.pdf import MEDIA_TYPE_PDF, exportar_pdf
from app.models.base import utcnow
from app.models.conflictos import ConflictoSesionDB
from app.repositories.carga import RepositorioAsignacionCarga
from app.repositories.conflictos import RepositorioConflicto
from app.repositories.horario import (
    RepositorioEscenario,
    RepositorioHorarioVersion,
    RepositorioSesion,
)
from app.repositories.procesos import RepositorioEjecucionSolver
from app.routers.comun import error, no_encontrado
from app.services import horario as servicio
from app.solver import resolver
from app.validator import MALLA_INCUMPLIDA, validar

router = APIRouter(tags=["horarios"])

SesionDB = Annotated[Session, Depends(get_session)]


# --- esquemas -----------------------------------------------------------------------


class VersionLeer(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    numero: int
    estado: EstadoVersion
    escenario_id: uuid.UUID | None
    nota: str | None
    publicado_at: Any = None


class VersionCrear(BaseModel):
    nota: str | None = None
    escenario_id: uuid.UUID | None = None
    # Copia las sesiones y el escenario de otra versión: el borrador para editar
    # una versión publicada (D-021) sin tocar la publicada.
    copiar_de: uuid.UUID | None = None


class EscenarioCrear(BaseModel):
    nombre: str = Field(min_length=1, max_length=120)
    descripcion: str | None = None


class SesionCrear(BaseModel):
    asignacion_carga_id: uuid.UUID
    dia: int = Field(ge=1, le=5)
    bloque_id: uuid.UUID
    docente_id: uuid.UUID | None = None
    recurso_id: uuid.UUID | None = None
    fijada: bool = False


class SesionMover(BaseModel):
    dia: int | None = Field(default=None, ge=1, le=5)
    bloque_id: uuid.UUID | None = None
    docente_id: uuid.UUID | None = None
    recurso_id: uuid.UUID | None = None
    fijada: bool | None = None


class ValidarCuerpo(BaseModel):
    al_publicar: bool = False


class EscenarioCuerpo(BaseModel):
    escenario_id: uuid.UUID
    aplicar: bool = False


class GenerarCuerpo(BaseModel):
    modo_docente: str = "habilitados"
    escenario_id: uuid.UUID | None = None
    solo_curso_id: uuid.UUID | None = None
    limpiar: bool = False


# --- escenarios ---------------------------------------------------------------------


@router.get("/escenarios", response_model=list[dict])
def listar_escenarios(sesion: SesionDB) -> list[dict]:
    return [
        {"id": str(escenario.id), "nombre": escenario.nombre, "descripcion": escenario.descripcion}
        for escenario in RepositorioEscenario(sesion).listar()
    ]


@router.post("/escenarios", status_code=201)
def crear_escenario(datos: EscenarioCrear, sesion: SesionDB) -> dict:
    repo = RepositorioEscenario(sesion)
    if repo.obtener_por_nombre(datos.nombre) is not None:
        error(409, "NOMBRE_DUPLICADO", "Ya existe un escenario con ese nombre.")
    escenario = repo.agregar(Escenario(nombre=datos.nombre, descripcion=datos.descripcion))
    sesion.commit()
    return {
        "id": str(escenario.id),
        "nombre": escenario.nombre,
        "descripcion": escenario.descripcion,
    }


# --- versiones ----------------------------------------------------------------------


@router.get("/horarios", response_model=list[VersionLeer])
def listar_versiones(sesion: SesionDB) -> list[HorarioVersion]:
    return sorted(RepositorioHorarioVersion(sesion).listar(), key=lambda version: version.numero)


@router.post("/horarios", response_model=VersionLeer, status_code=201)
def crear_version(datos: VersionCrear, sesion: SesionDB) -> HorarioVersion:
    version = servicio.crear_version(
        sesion, datos.nota, datos.escenario_id, datos.copiar_de
    )
    sesion.commit()
    return version


@router.get("/horarios/{version_id}", response_model=VersionLeer)
def leer_version(version_id: uuid.UUID, sesion: SesionDB) -> HorarioVersion:
    return servicio.obtener_version(sesion, version_id)


@router.get("/horarios/{version_id}/vista")
def vista(
    version_id: uuid.UUID,
    sesion: SesionDB,
    por: Annotated[str, Query(pattern="^(curso|docente|recurso)$")] = "curso",
    id: uuid.UUID | None = None,
) -> dict:
    """Sesiones de la versión, filtradas por curso, docente o recurso."""
    servicio.obtener_version(sesion, version_id)
    sesiones = RepositorioSesion(sesion).listar_por_version(version_id)
    if id is not None:
        sesiones = [item for item in sesiones if getattr(item, f"{por}_id") == id]
    return {"por": por, "sesiones": [servicio.datos_sesion(item) for item in sesiones]}


# --- sesiones -----------------------------------------------------------------------


@router.post("/horarios/{version_id}/sesiones", status_code=201)
def colocar_sesion(version_id: uuid.UUID, datos: SesionCrear, sesion: SesionDB) -> dict:
    version = servicio.obtener_version(sesion, version_id)
    creada = servicio.crear_sesion(sesion, version, **datos.model_dump())
    sesion.commit()
    return servicio.datos_sesion(creada)


@router.patch("/horarios/{version_id}/sesiones/{sesion_id}")
def mover_sesion(
    version_id: uuid.UUID, sesion_id: uuid.UUID, datos: SesionMover, sesion: SesionDB
) -> dict:
    version = servicio.obtener_version(sesion, version_id)
    cambios = {clave: valor for clave, valor in datos.model_dump().items() if valor is not None}
    movida = servicio.mover_sesion(sesion, version, sesion_id, cambios)
    sesion.commit()
    return servicio.datos_sesion(movida)


@router.delete("/horarios/{version_id}/sesiones/{sesion_id}", status_code=204)
def quitar_sesion(version_id: uuid.UUID, sesion_id: uuid.UUID, sesion: SesionDB) -> None:
    version = servicio.obtener_version(sesion, version_id)
    servicio.eliminar_sesion(sesion, version, sesion_id)
    sesion.commit()


# --- validación, generación y publicación -------------------------------------------


def _conflictos_json(sesion: Session, version_id: uuid.UUID) -> list[dict]:
    conflictos = RepositorioConflicto(sesion).listar_por_version(version_id)
    vinculos: dict[uuid.UUID, list[str]] = {}
    filas = sesion.scalars(
        sa.select(ConflictoSesionDB).where(
            ConflictoSesionDB.conflicto_id.in_([conflicto.id for conflicto in conflictos])
        )
    ).all()
    for fila in filas:
        vinculos.setdefault(fila.conflicto_id, []).append(str(fila.sesion_id))
    return [
        {
            "id": str(conflicto.id),
            "codigo": conflicto.codigo,
            "gravedad": str(conflicto.gravedad),
            "estado": str(conflicto.estado),
            "mensaje": conflicto.mensaje,
            "sesion_ids": vinculos.get(conflicto.id, []),
        }
        for conflicto in conflictos
    ]


@router.post("/horarios/{version_id}/validar")
def validar_version(
    version_id: uuid.UUID, sesion: SesionDB, datos: ValidarCuerpo | None = None
) -> dict:
    version = servicio.obtener_version(sesion, version_id)
    al_publicar = bool(datos.al_publicar) if datos else False
    servicio.guardar_conflictos(sesion, version, al_publicar)
    sesion.commit()
    return {"conflictos": _conflictos_json(sesion, version_id)}


@router.get("/horarios/{version_id}/conflictos")
def listar_conflictos(version_id: uuid.UUID, sesion: SesionDB) -> dict:
    servicio.obtener_version(sesion, version_id)
    return {"conflictos": _conflictos_json(sesion, version_id)}


@router.post("/horarios/{version_id}/generar")
async def generar(version_id: uuid.UUID, datos: GenerarCuerpo, sesion: SesionDB) -> dict:
    version = servicio.obtener_version(sesion, version_id)
    servicio.exigir_borrador(version)
    if datos.escenario_id is not None:
        version = replace(version, escenario_id=datos.escenario_id)
        version = RepositorioHorarioVersion(sesion).actualizar(version)
    estado = servicio.cargar_estado(sesion, version)
    # Pin (D-017): si el usuario fijó algo, el solver mueve todo lo demás. Sin ningún
    # pin se mantiene D-008: las sesiones existentes no se tocan.
    fijas = [item for item in estado.sesiones if item.fijada] or None
    inicio = utcnow()
    resultado = await run_in_threadpool(
        partial(
            resolver,
            estado,
            datos.modo_docente,
            version.escenario_id,
            fijas,
            datos.solo_curso_id,
            datos.limpiar,
            None,
            horario_version_id=version.id,
        )
    )
    RepositorioEjecucionSolver(sesion).agregar(
        EjecucionSolver(
            horario_version_id=version.id,
            modo_docente=datos.modo_docente,
            estado=str(resultado.estado),
            diagnostico={"diagnostico": [asdict(item) for item in resultado.diagnostico]},
            iniciado_at=inicio,
            terminado_at=utcnow(),
        )
    )
    if resultado.sesiones:
        servicio.persistir_plan(sesion, version, resultado)
    servicio.guardar_conflictos(sesion, version)
    if resultado.diagnostico and not resultado.sesiones:
        servicio.guardar_diagnosticos(sesion, version, list(resultado.diagnostico))
    sesion.commit()
    return {
        "estado": str(resultado.estado),
        "sesiones": len(resultado.sesiones),
        "objetivo": resultado.objetivo,
        "diagnostico": [
            {
                "codigo": item.codigo,
                "gravedad": str(item.gravedad),
                "mensaje": item.mensaje,
                "docente_codigo": item.docente_codigo,
            }
            for item in resultado.diagnostico
        ],
        "conflictos": _conflictos_json(sesion, version.id),
    }


@router.post("/horarios/{version_id}/escenario")
async def probar_escenario(
    version_id: uuid.UUID, datos: EscenarioCuerpo, sesion: SesionDB
) -> dict:
    """Vista previa y aplicación del escenario "¿y si…?".

    Con `aplicar=false` no escribe nada: resuelve con el overlay, cuenta las sesiones
    afectadas y devuelve el prospecto. Con `aplicar=true` fija `horario_version.escenario_id`
    (D-010: la versión es la única verdad) y persiste el plan.
    """
    version = servicio.obtener_version(sesion, version_id)
    servicio.exigir_borrador(version)
    escenario = RepositorioEscenario(sesion).obtener(datos.escenario_id)
    if escenario is None:
        no_encontrado("Escenario")

    # El overlay del escenario se carga aunque la versión todavía no lo tenga aplicado.
    estado = servicio.cargar_estado(sesion, version, escenario.id)
    afectadas = servicio.afectadas_por_escenario(sesion, estado, escenario.id)
    # Re-planificación completa salvo lo que el usuario fijó a mano (D-017). Fijar "las no
    # afectadas" (D-005 original) deja una sola franja libre con la grilla llena y el
    # escenario sale INFACTIBLE por construcción: ver la corrección de D-005.
    fijas = [item for item in estado.sesiones if item.fijada]
    resultado = await run_in_threadpool(
        partial(
            resolver,
            estado,
            "habilitados",
            escenario.id,
            fijas,
            None,
            False,
            None,
            horario_version_id=version.id,
        )
    )

    if datos.aplicar:
        publicada = RepositorioHorarioVersion(sesion).actualizar(
            replace(version, escenario_id=escenario.id)
        )
        if resultado.sesiones:
            servicio.persistir_plan(sesion, publicada, resultado)
        servicio.guardar_conflictos(sesion, publicada)
        sesion.commit()
        conflictos = _conflictos_json(sesion, version.id)
    else:
        prospecto = replace(estado, sesiones=tuple(resultado.sesiones))
        conflictos = [
            {
                "codigo": hallazgo.codigo,
                "gravedad": str(hallazgo.gravedad),
                "mensaje": hallazgo.mensaje,
                "sesion_ids": [str(item) for item in hallazgo.sesion_ids],
            }
            for hallazgo in validar(prospecto, escenario.id)
        ]

    return {
        "escenario": {"id": str(escenario.id), "nombre": escenario.nombre},
        "aplicado": datos.aplicar,
        "sesiones_afectadas": len(afectadas),
        "resultado": {
            "estado": str(resultado.estado),
            "sesiones": len(resultado.sesiones),
            "objetivo": resultado.objetivo,
            "diagnostico": [
                {"codigo": item.codigo, "gravedad": str(item.gravedad), "mensaje": item.mensaje}
                for item in resultado.diagnostico
            ],
        },
        "conflictos": conflictos,
    }


@router.post("/horarios/{version_id}/publicar", response_model=VersionLeer)
def publicar_version(version_id: uuid.UUID, sesion: SesionDB) -> HorarioVersion:
    version = servicio.obtener_version(sesion, version_id)
    publicada = servicio.publicar(sesion, version)
    sesion.commit()
    return publicada


# --- conflictos -> propuestas -------------------------------------------------------


@router.post("/conflictos/{conflicto_id}/propuestas")
def crear_propuestas(conflicto_id: uuid.UUID, sesion: SesionDB) -> dict:
    resultado = servicio.proponer(sesion, conflicto_id)
    sesion.commit()
    return resultado


@router.post("/propuestas/{propuesta_id}/aceptar")
def aceptar_propuesta(propuesta_id: uuid.UUID, sesion: SesionDB) -> dict:
    propuesta = servicio.aceptar_propuesta(sesion, propuesta_id)
    sesion.commit()
    return {"id": str(propuesta.id), "estado": str(propuesta.estado)}


@router.post("/propuestas/{propuesta_id}/rechazar")
def rechazar_propuesta(propuesta_id: uuid.UUID, sesion: SesionDB) -> dict:
    propuesta = servicio.rechazar_propuesta(sesion, propuesta_id)
    sesion.commit()
    return {"id": str(propuesta.id), "estado": str(propuesta.estado)}


# --- deshacer, rehacer, arrastre y exportación --------------------------------------


@router.post("/horarios/{version_id}/deshacer")
def deshacer(version_id: uuid.UUID, sesion: SesionDB) -> dict:
    version = servicio.obtener_version(sesion, version_id)
    resultado = servicio.deshacer(sesion, version)
    sesion.commit()
    return resultado


@router.post("/horarios/{version_id}/rehacer")
def rehacer(version_id: uuid.UUID, sesion: SesionDB) -> dict:
    version = servicio.obtener_version(sesion, version_id)
    resultado = servicio.rehacer(sesion, version)
    sesion.commit()
    return resultado


@router.get("/horarios/{version_id}/arrastre")
def arrastre(
    version_id: uuid.UUID, asignacion_id: uuid.UUID, sesion: SesionDB
) -> dict:
    """Estado de cada franja para arrastrar esa asignatura: válida, advertencia o bloqueada.

    shortcut: 30 `validar()` completos por request (~50 ms). Si la grilla lo pide por
    cada movimiento, cachear las reglas que no dependen de la sesión.
    """
    version = servicio.obtener_version(sesion, version_id)
    asignacion = RepositorioAsignacionCarga(sesion).obtener(asignacion_id)
    if asignacion is None:
        error(400, "REFERENCIA_INVALIDA", "Asignación inexistente.")
    estado = servicio.cargar_estado(sesion, version)
    bloques = sorted(
        (bloque for bloque in estado.bloques if bloque.tipo == "clase"),
        key=lambda bloque: bloque.orden,
    )
    celdas = []
    for bloque in bloques:
        for dia in range(1, 6):
            prueba = Sesion(
                horario_version_id=version.id,
                asignacion_carga_id=asignacion.id,
                curso_id=asignacion.curso_id,
                docente_id=asignacion.docente_principal_id,
                dia=dia,
                bloque_id=bloque.id,
            )
            con_prueba = replace(estado, sesiones=(*estado.sesiones, prueba))
            hallazgos = validar(con_prueba, version.escenario_id)
            # MALLA_INCUMPLIDA describe el avance de la semana completa, no la celda:
            # incluirla pintaría las 30 franjas como "Revisar" hasta el último movimiento.
            propios = [
                item
                for item in hallazgos
                if prueba.id in item.sesion_ids and item.codigo != MALLA_INCUMPLIDA
            ]
            errores = [item for item in propios if item.gravedad == Gravedad.error]
            celdas.append(
                {
                    "dia": dia,
                    "bloque_id": str(bloque.id),
                    "estado": "bloqueada" if errores else ("advertencia" if propios else "valida"),
                    "motivo": " ".join(item.mensaje for item in (errores or propios)[:2]) or None,
                }
            )
    return {"celdas": celdas}


@router.get("/horarios/{version_id}/exportar")
def exportar(
    version_id: uuid.UUID,
    sesion: SesionDB,
    formato: Annotated[str, Query(pattern="^(xlsx|pdf)$")] = "xlsx",
    por: Annotated[str, Query(pattern="^(curso|docente|recurso|general)$")] = "general",
    id: uuid.UUID | None = None,
) -> Response:
    version = servicio.obtener_version(sesion, version_id)
    estado = servicio.cargar_estado(sesion, version)
    if formato == "pdf":
        pdf = exportar_pdf(estado, list(estado.sesiones), por, id)
        return Response(
            content=pdf,
            media_type=MEDIA_TYPE_PDF,
            headers={"Content-Disposition": f'attachment; filename="horario-{por}.pdf"'},
        )
    libro = exportar_xlsx(estado, list(estado.sesiones), por, id)
    return Response(
        content=libro,
        media_type=MEDIA_TYPE_XLSX,
        headers={"Content-Disposition": f'attachment; filename="horario-{por}.xlsx"'},
    )
