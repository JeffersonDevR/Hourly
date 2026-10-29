"""Reglas de la versión de horario: estado, sesiones, conflictos, plan y deshacer.

Todo lo que escribe `sesion` pasa por acá. Las invariantes DURAS las impone la DB
(D-001) y se traducen a `409`; las reglas del validador se evalúan al vuelo y nunca
bloquean (D-011).

Los servicios hacen `flush()`, nunca `commit()`: la transacción la cierra el router
(misma regla que `app.services.historial`).
"""

from __future__ import annotations

import uuid
from dataclasses import asdict, replace
from typing import Any, NoReturn

import sqlalchemy as sa
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.domain.conflictos import Conflicto as ConflictoDominio
from app.domain.conflictos import ConflictoSesion, PropuestaCambio, PropuestaResolucion
from app.domain.enums import (
    EstadoConflicto,
    EstadoPropuesta,
    EstadoVersion,
    Gravedad,
    OrigenPropuesta,
)
from app.domain.horario import HorarioVersion, Sesion
from app.models.base import utcnow
from app.models.conflictos import ConflictoDB, ConflictoSesionDB
from app.models.historial import HistorialCambioDB
from app.models.horario import HorarioVersionDB
from app.repositories.carga import (
    RepositorioAsignacionCarga,
    RepositorioDisponibilidad,
)
from app.repositories.catalogo import (
    RepositorioAptitud,
    RepositorioAsignatura,
    RepositorioBloque,
    RepositorioCurso,
    RepositorioDocente,
)
from app.repositories.conflictos import (
    RepositorioConflicto,
    RepositorioConflictoSesion,
    RepositorioPropuesta,
    RepositorioPropuestaCambio,
)
from app.repositories.horario import (
    RepositorioEscenario,
    RepositorioEscenarioCambio,
    RepositorioHorarioVersion,
    RepositorioSesion,
)
from app.repositories.recursos import RepositorioRecurso
from app.routers.comun import error, no_encontrado
from app.services.historial import registrar_cambio
from app.services.ia import proponer_con_ia
from app.solver import reparar_greedy
from app.solver.resultado import Resultado
from app.validator import (
    CURSO_DOBLE,
    DOCENTE_DOBLE,
    RECURSO_DOBLE,
    EstadoHorario,
    diagnosticar_carga,
    validar,
)

#: Las tres invariantes duras de `sesion` (D-001) y el código que las nombra.
_UNIQUE_A_CODIGO = (
    ("sesion.docente_id", DOCENTE_DOBLE),
    ("sesion.curso_id", CURSO_DOBLE),
    ("sesion.recurso_id", RECURSO_DOBLE),
)

# --- traducción de errores de la DB -------------------------------------------------


def _choque(exc: IntegrityError) -> NoReturn:
    """`UNIQUE(...)` de `sesion` -> conflicto de dominio con nombre propio."""
    mensaje = str(exc.orig)
    for columna, codigo in _UNIQUE_A_CODIGO:
        if columna in mensaje:
            error(409, codigo, "Esa franja ya está ocupada para ese docente, curso o recurso.")
    error(409, "SESION_DUPLICADA", "La sesión choca con otra ya colocada.")


def _mutar(sesion: Session, cambio: Any) -> Any:
    """SAVEPOINT alrededor de la escritura: un choque de UNIQUE no rompe la request."""
    try:
        with sesion.begin_nested():
            resultado = cambio()
    except IntegrityError as exc:
        _choque(exc)
    return resultado


# --- estado -------------------------------------------------------------------------


def cargar_estado(
    sesion: Session,
    version: HorarioVersion | None = None,
    escenario_id: uuid.UUID | None = None,
) -> EstadoHorario:
    """Foto del horario para el validador y el solver. Sin versión: catálogo y carga.

    `escenario_id` permite cargar el overlay de un escenario que la versión **todavía no
    tiene aplicado**: es la vista previa de "¿y si…?". Sin ese parámetro el estado sale
    sin `escenario_cambios` y el solver resolvería a ciegas.
    """
    escenario_id = escenario_id or (version.escenario_id if version else None)
    return EstadoHorario(
        cursos=tuple(RepositorioCurso(sesion).listar()),
        docentes=tuple(RepositorioDocente(sesion).listar()),
        bloques=tuple(RepositorioBloque(sesion).listar()),
        asignaturas=tuple(RepositorioAsignatura(sesion).listar()),
        aptitudes=tuple(RepositorioAptitud(sesion).listar()),
        asignaciones=tuple(RepositorioAsignacionCarga(sesion).listar()),
        bloqueos=tuple(RepositorioDisponibilidad(sesion).listar()),
        recursos=tuple(RepositorioRecurso(sesion).listar()),
        escenario_cambios=(
            tuple(RepositorioEscenarioCambio(sesion).listar_por_escenario(escenario_id))
            if escenario_id
            else ()
        ),
        sesiones=(
            tuple(RepositorioSesion(sesion).listar_por_version(version.id))
            if version
            else ()
        ),
    )


def obtener_version(sesion: Session, version_id: uuid.UUID) -> HorarioVersion:
    version = RepositorioHorarioVersion(sesion).obtener(version_id)
    if version is None:
        no_encontrado("Versión de horario")
    return version


def crear_version(
    sesion: Session,
    nota: str | None,
    escenario_id: uuid.UUID | None,
    copiar_de: uuid.UUID | None = None,
) -> HorarioVersion:
    if (
        escenario_id is not None
        and RepositorioEscenario(sesion).obtener(escenario_id) is None
    ):
        error(400, "REFERENCIA_INVALIDA", "Escenario inexistente.")
    origen = obtener_version(sesion, copiar_de) if copiar_de is not None else None
    ultimo = sesion.scalar(sa.select(sa.func.max(HorarioVersionDB.numero)))
    version = HorarioVersion(
        numero=(ultimo or 0) + 1,
        estado=EstadoVersion.borrador,
        nota=nota,
        escenario_id=(
            escenario_id if escenario_id is not None else (origen.escenario_id if origen else None)
        ),
    )
    guardada = RepositorioHorarioVersion(sesion).agregar(version)

    if origen is not None:
        # El borrador arranca con el trabajo de la versión anterior, que queda intacta.
        repo_sesion = RepositorioSesion(sesion)
        for previa in repo_sesion.listar_por_version(origen.id):
            repo_sesion.agregar(
                replace(
                    previa,
                    id=uuid.uuid4(),
                    horario_version_id=guardada.id,
                    created_at=None,
                    updated_at=None,
                )
            )
    return guardada


def exigir_borrador(version: HorarioVersion) -> None:
    """Una versión publicada es inmutable: se edita en un borrador nuevo (fase 9)."""
    if version.estado is not EstadoVersion.borrador:
        error(
            409,
            "VERSION_PUBLICADA",
            "La versión está publicada: creá un borrador nuevo para editarla.",
        )


# --- sesiones -----------------------------------------------------------------------


def datos_sesion(sesion: Sesion) -> dict[str, Any]:
    """Forma serializable que guarda `historial_cambio.antes/despues`."""
    return {
        "id": str(sesion.id),
        "horario_version_id": str(sesion.horario_version_id),
        "asignacion_carga_id": str(sesion.asignacion_carga_id),
        "curso_id": str(sesion.curso_id),
        "docente_id": str(sesion.docente_id),
        "dia": sesion.dia,
        "bloque_id": str(sesion.bloque_id),
        "recurso_id": str(sesion.recurso_id) if sesion.recurso_id else None,
        "fijada": sesion.fijada,
    }


def sesion_desde(datos: dict[str, Any]) -> Sesion:
    return Sesion(
        id=uuid.UUID(datos["id"]),
        horario_version_id=uuid.UUID(datos["horario_version_id"]),
        asignacion_carga_id=uuid.UUID(datos["asignacion_carga_id"]),
        curso_id=uuid.UUID(datos["curso_id"]),
        docente_id=uuid.UUID(datos["docente_id"]),
        dia=int(datos["dia"]),
        bloque_id=uuid.UUID(datos["bloque_id"]),
        recurso_id=uuid.UUID(datos["recurso_id"]) if datos["recurso_id"] else None,
        fijada=bool(datos.get("fijada", False)),
    )


def _registrar(
    sesion: Session,
    version_id: uuid.UUID,
    accion: str,
    antes: dict[str, Any] | None = None,
    despues: dict[str, Any] | None = None,
) -> None:
    """Toda mutación borra la pila de rehacer: el redo no sobrevive a otra edición."""
    sesion.execute(
        sa.delete(HistorialCambioDB).where(
            HistorialCambioDB.horario_version_id == version_id,
            HistorialCambioDB.deshecho.is_(True),
        )
    )
    registrar_cambio(
        sesion,
        entidad="sesion",
        entidad_id=(despues or antes or {})["id"],
        accion=accion,
        antes=antes,
        despues=despues,
        horario_version_id=version_id,
    )


def _bloque_de_clase(sesion: Session, bloque_id: uuid.UUID) -> None:
    bloque = RepositorioBloque(sesion).obtener(bloque_id)
    if bloque is None:
        error(400, "REFERENCIA_INVALIDA", "Bloque inexistente.")
    if bloque.tipo != "clase":
        error(400, "BLOQUE_NO_CLASE", "Ese bloque es descanso o almuerzo: no admite sesiones.")


def crear_sesion(
    sesion: Session,
    version: HorarioVersion,
    *,
    asignacion_carga_id: uuid.UUID,
    dia: int,
    bloque_id: uuid.UUID,
    docente_id: uuid.UUID | None = None,
    recurso_id: uuid.UUID | None = None,
    fijada: bool = False,
) -> Sesion:
    exigir_borrador(version)
    asignacion = RepositorioAsignacionCarga(sesion).obtener(asignacion_carga_id)
    if asignacion is None:
        error(400, "REFERENCIA_INVALIDA", "Asignación inexistente.")
    _bloque_de_clase(sesion, bloque_id)
    # Maestro de la asignación por defecto: el caso normal no repite el dato.
    sesion_nueva = Sesion(
        horario_version_id=version.id,
        asignacion_carga_id=asignacion.id,
        curso_id=asignacion.curso_id,
        docente_id=docente_id or asignacion.docente_principal_id,
        dia=dia,
        bloque_id=bloque_id,
        recurso_id=recurso_id,
        fijada=fijada,
    )
    guardada = _mutar(sesion, lambda: RepositorioSesion(sesion).agregar(sesion_nueva))
    _registrar(sesion, version.id, "crear", despues=datos_sesion(guardada))
    return guardada


def mover_sesion(
    sesion: Session,
    version: HorarioVersion,
    sesion_id: uuid.UUID,
    cambios: dict[str, Any],
) -> Sesion:
    exigir_borrador(version)
    repo = RepositorioSesion(sesion)
    actual = repo.obtener(sesion_id)
    if actual is None or actual.horario_version_id != version.id:
        no_encontrado("Sesión")
    if "bloque_id" in cambios:
        _bloque_de_clase(sesion, cambios["bloque_id"])
    movida = replace(actual, **cambios)
    guardada = _mutar(sesion, lambda: repo.actualizar(movida))
    _registrar(
        sesion, version.id, "mover", antes=datos_sesion(actual), despues=datos_sesion(guardada)
    )
    return guardada


def eliminar_sesion(sesion: Session, version: HorarioVersion, sesion_id: uuid.UUID) -> None:
    exigir_borrador(version)
    repo = RepositorioSesion(sesion)
    actual = repo.obtener(sesion_id)
    if actual is None or actual.horario_version_id != version.id:
        no_encontrado("Sesión")
    repo.eliminar(sesion_id)
    _registrar(sesion, version.id, "eliminar", antes=datos_sesion(actual))


# --- conflictos ---------------------------------------------------------------------


def guardar_conflictos(
    sesion: Session, version: HorarioVersion, al_publicar: bool = False
) -> list[ConflictoDominio]:
    """Autoritativo (D-011): borra los conflictos de la versión y los regenera."""
    hallazgos = validar(cargar_estado(sesion, version), version.escenario_id, al_publicar)
    sesion.execute(
        sa.delete(ConflictoDB).where(ConflictoDB.horario_version_id == version.id)
    )
    repo_conflicto = RepositorioConflicto(sesion)
    repo_vinculo = RepositorioConflictoSesion(sesion)
    guardados: list[ConflictoDominio] = []
    for hallazgo in hallazgos:
        guardado = repo_conflicto.agregar(
            ConflictoDominio(
                horario_version_id=version.id,
                codigo=hallazgo.codigo,
                gravedad=hallazgo.gravedad,
                mensaje=hallazgo.mensaje,
                estado=EstadoConflicto.abierto,
                detectado_at=utcnow(),
            )
        )
        for sesion_id in hallazgo.sesion_ids:
            repo_vinculo.agregar(ConflictoSesion(conflicto_id=guardado.id, sesion_id=sesion_id))
        guardados.append(guardado)
    return guardados


def guardar_diagnosticos(
    sesion: Session, version: HorarioVersion, diagnostico: list[Any]
) -> None:
    """Expone en `/conflictos` por qué el solver no pudo (D-003 paso 4).

    `diagnosticar_carga` no se persiste antes de generar porque no hay versión (D-007),
    pero cuando la generación falla **sí** hay versión y el usuario necesita ver el motivo
    en el mismo lugar donde resuelve todo lo demás.
    """
    repo = RepositorioConflicto(sesion)
    for item in diagnostico:
        repo.agregar(
            ConflictoDominio(
                horario_version_id=version.id,
                codigo=item.codigo,
                gravedad=item.gravedad,
                mensaje=item.mensaje,
                estado=EstadoConflicto.abierto,
                detectado_at=utcnow(),
                detalle={
                    "docente_codigo": item.docente_codigo,
                    "demanda": item.demanda,
                    "maximo": item.maximo,
                    "franjas": item.franjas,
                    "asignatura": item.asignatura,
                },
            )
        )


# --- generar ------------------------------------------------------------------------


def persistir_plan(sesion: Session, version: HorarioVersion, resultado: Resultado) -> None:
    """Reemplaza las sesiones de la versión con el plan, en dos fases.

    Borrar todo antes de insertar no es pereza: un plan puede **intercambiar** dos sesiones
    de franja (A→B, B→A), y actualizar fila por fila choca contra
    `UNIQUE(version, día, bloque, docente|curso)` cuando A intenta ocupar la franja que B
    todavía no soltó. Los ids se conservan igual: las fijas vienen con el suyo y las
    generadas usan `uuid5(versión, asignación, día, bloque)`.
    """
    repo = RepositorioSesion(sesion)
    for actual in repo.listar_por_version(version.id):
        repo.eliminar(actual.id)
    for plan in resultado.sesiones:
        repo.agregar(plan)


def publicar(sesion: Session, version: HorarioVersion) -> HorarioVersion:
    hallazgos = guardar_conflictos(sesion, version, al_publicar=True)
    errores = [hallazgo.mensaje for hallazgo in hallazgos if hallazgo.gravedad == Gravedad.error]
    if errores:
        error(409, "CONFLICTOS_ABIERTOS", " ".join(errores[:5]))
    publicada = replace(version, estado=EstadoVersion.publicado, publicado_at=utcnow())
    return RepositorioHorarioVersion(sesion).actualizar(publicada)


# --- escenarios (D-005, D-010) ------------------------------------------------------


def afectadas_por_escenario(
    sesion: Session, estado: EstadoHorario, escenario_id: uuid.UUID
) -> set[uuid.UUID]:
    """Sesiones que caen en una franja que el escenario vuelve no disponible."""
    cambios = RepositorioEscenarioCambio(sesion).listar_por_escenario(escenario_id)
    franjas = {
        (cambio.docente_id, cambio.dia, cambio.bloque_id)
        for cambio in cambios
        if not cambio.disponible_nuevo
    }
    return {
        sesion_horario.id
        for sesion_horario in estado.sesiones
        if (sesion_horario.docente_id, sesion_horario.dia, sesion_horario.bloque_id) in franjas
    }


# --- deshacer / rehacer -------------------------------------------------------------


def _ultima_entrada(sesion: Session, version_id: uuid.UUID, deshecha: bool) -> Any:
    return sesion.scalars(
        sa.select(HistorialCambioDB)
        .where(
            HistorialCambioDB.horario_version_id == version_id,
            HistorialCambioDB.deshecho.is_(deshecha),
        )
        .order_by(HistorialCambioDB.ocurrido_at.desc(), HistorialCambioDB.created_at.desc())
    ).first()


def _reinsertar(sesion: Session, datos: dict[str, Any]) -> None:
    repo = RepositorioSesion(sesion)
    if repo.obtener(uuid.UUID(datos["id"])) is None:
        repo.agregar(sesion_desde(datos))


def _aplicar_entrada(
    sesion: Session, version: HorarioVersion, entrada: HistorialCambioDB, inverso: bool
) -> None:
    antes = entrada.antes or {}
    despues = entrada.despues or {}
    objetivo = antes if inverso else despues
    if entrada.accion == "crear":
        if inverso:
            RepositorioSesion(sesion).eliminar(uuid.UUID(antes.get("id", despues["id"])))
        else:
            _reinsertar(sesion, despues)
    elif entrada.accion == "eliminar":
        if inverso:
            _reinsertar(sesion, antes)
        else:
            RepositorioSesion(sesion).eliminar(uuid.UUID(antes["id"]))
    else:  # mover
        actual = RepositorioSesion(sesion).obtener(uuid.UUID(objetivo["id"]))
        if actual is not None:
            RepositorioSesion(sesion).actualizar(sesion_desde(objetivo))


def deshacer(sesion: Session, version: HorarioVersion) -> dict[str, Any]:
    exigir_borrador(version)
    entrada = _ultima_entrada(sesion, version.id, deshecha=False)
    if entrada is None:
        error(409, "NADA_QUE_DESHACER", "No hay cambios para deshacer en esta versión.")
    _aplicar_entrada(sesion, version, entrada, inverso=True)
    entrada.deshecho = True
    sesion.flush()
    return {"accion": entrada.accion, "entidad_id": entrada.entidad_id, "deshecho": True}


def rehacer(sesion: Session, version: HorarioVersion) -> dict[str, Any]:
    exigir_borrador(version)
    entrada = _ultima_entrada(sesion, version.id, deshecha=True)
    if entrada is None:
        error(409, "NADA_QUE_REHACER", "No hay cambios para rehacer en esta versión.")
    _aplicar_entrada(sesion, version, entrada, inverso=False)
    entrada.deshecho = False
    sesion.flush()
    return {"accion": entrada.accion, "entidad_id": entrada.entidad_id, "rehecho": True}


# --- propuestas (D-003: determinista antes que IA) ----------------------------------


def proponer(sesion: Session, conflicto_id: uuid.UUID) -> dict[str, Any]:
    """Greedy primero. Sin propuestas válidas, alerta con la causa aritmética."""
    conflicto = RepositorioConflicto(sesion).obtener(conflicto_id)
    if conflicto is None:
        no_encontrado("Conflicto")
    version = obtener_version(sesion, conflicto.horario_version_id)
    estado = cargar_estado(sesion, version)
    cambios = reparar_greedy(estado, version.escenario_id)
    if not cambios:
        # Paso 3 de D-003. El paso CP-SAT con `fijas` llega con el flujo de escenarios (fase 9).
        de_ia = proponer_con_ia(
            sesion,
            estado,
            {
                "codigo": conflicto.codigo,
                "mensaje": conflicto.mensaje,
                "sesion_ids": _sesiones_del_conflicto(sesion, conflicto.id),
            },
            version.escenario_id,
            conflicto.id,
        )
        if de_ia:
            repo_cambios = RepositorioPropuestaCambio(sesion)
            return {
                "propuestas": [
                    _propuesta_json(propuesta, repo_cambios.listar_por_propuesta(propuesta.id))
                    for propuesta in de_ia
                ],
                "alerta": [],
            }
        alerta = [asdict(diagnostico) for diagnostico in diagnosticar_carga(estado)]
        return {"propuestas": [], "alerta": alerta}
    propuesta = RepositorioPropuesta(sesion).agregar(
        PropuestaResolucion(
            origen=OrigenPropuesta.solver,
            titulo="Reacomodo automático",
            explicacion=f"Se mueven {len(cambios)} sesión(es) a una franja libre y válida.",
            impacto="Ninguna sesión fija se toca.",
            conflicto_id=conflicto.id,
        )
    )
    repo_cambio = RepositorioPropuestaCambio(sesion)
    guardados = [
        repo_cambio.agregar(
            PropuestaCambio(
                propuesta_id=propuesta.id,
                tipo=cambio.tipo,
                sesion_id=cambio.sesion_id,
                datos={
                    clave: str(valor) if isinstance(valor, uuid.UUID) else valor
                    for clave, valor in (
                        ("dia", cambio.dia),
                        ("bloque_id", cambio.bloque_id),
                        ("docente_id", cambio.docente_id),
                        ("recurso_id", cambio.recurso_id),
                    )
                    if valor is not None
                },
            )
        )
        for cambio in cambios
    ]
    return {"propuestas": [_propuesta_json(propuesta, guardados)], "alerta": []}


def _sesiones_del_conflicto(sesion: Session, conflicto_id: uuid.UUID) -> list[str]:
    filas = sesion.scalars(
        sa.select(ConflictoSesionDB).where(ConflictoSesionDB.conflicto_id == conflicto_id)
    ).all()
    return [str(fila.sesion_id) for fila in filas]


def _propuesta_json(propuesta: Any, cambios: list[Any]) -> dict[str, Any]:
    return {
        "id": str(propuesta.id),
        "origen": str(propuesta.origen),
        "titulo": propuesta.titulo,
        "explicacion": propuesta.explicacion,
        "impacto": propuesta.impacto,
        "estado": str(propuesta.estado),
        "cambios": [
            {"id": str(cambio.id), "tipo": str(cambio.tipo), "datos": cambio.datos}
            for cambio in cambios
        ],
    }


def _transicion(
    sesion: Session, propuesta_id: uuid.UUID, destino: EstadoPropuesta
) -> PropuestaResolucion:
    repo = RepositorioPropuesta(sesion)
    propuesta = repo.obtener(propuesta_id)
    if propuesta is None:
        no_encontrado("Propuesta")
    if propuesta.estado is not EstadoPropuesta.pendiente:
        error(409, "PROPUESTA_CERRADA", "La propuesta ya fue aceptada o rechazada.")
    return repo.actualizar(replace(propuesta, estado=destino))


def aceptar_propuesta(sesion: Session, propuesta_id: uuid.UUID) -> PropuestaResolucion:
    repo = RepositorioPropuesta(sesion)
    propuesta = repo.obtener(propuesta_id)
    if propuesta is None:
        no_encontrado("Propuesta")
    if propuesta.conflicto_id is None:
        error(409, "PROPUESTA_INVALIDA", "La propuesta no cuelga de un conflicto.")
    conflicto = RepositorioConflicto(sesion).obtener(propuesta.conflicto_id)
    if conflicto is None:
        no_encontrado("Conflicto")
    version = obtener_version(sesion, conflicto.horario_version_id)
    exigir_borrador(version)
    for cambio in RepositorioPropuestaCambio(sesion).listar_por_propuesta(propuesta.id):
        if cambio.sesion_id is None:
            continue
        mover_sesion(sesion, version, cambio.sesion_id, _cambios_tipados(cambio.datos))
    guardada = _transicion(sesion, propuesta.id, EstadoPropuesta.aceptada)
    guardar_conflictos(sesion, version)
    return guardada


def _cambios_tipados(datos: dict[str, Any]) -> dict[str, Any]:
    claves_uuid = ("bloque_id", "docente_id", "recurso_id")
    return {
        clave: uuid.UUID(valor) if clave in claves_uuid and valor else valor
        for clave, valor in datos.items()
    }


def rechazar_propuesta(sesion: Session, propuesta_id: uuid.UUID) -> PropuestaResolucion:
    return _transicion(sesion, propuesta_id, EstadoPropuesta.rechazada)

