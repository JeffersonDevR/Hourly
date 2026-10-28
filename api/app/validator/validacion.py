"""`validar`: conflictos del horario sobre `EstadoHorario`. Puro, sin DB ni IA.

Una sola función para todo el producto (`AGENTS.md`, regla 1): la API, el solver,
la importación y las propuestas de la IA validan acá. No hay I/O ni estado global.

Reglas que dependen del contexto:
- `escenario`: superpone `escenario_cambio` sobre `disponibilidad_bloqueo`. El
  escenario es un overlay, nunca un reemplazo (D-005). Sin escenario se valida el
  estado base.
- `al_publicar`: decide la gravedad devuelta de `MALLA_INCUMPLIDA` — advertencia
  mientras se edita, error al publicar (D-011). Una sola verdad, evaluada al vuelo.

`ASIGNATURA_PESADA_CONSECUTIVA` es la única regla blanda del validador: siempre
`advertencia`, nunca bloquea y nunca escala con `al_publicar` (D-006).
"""

import uuid
from collections import defaultdict

from app.domain.carga import AsignacionCarga
from app.domain.catalogo import Asignatura, Bloque, Curso, Docente
from app.domain.enums import Gravedad, TipoBloque
from app.domain.horario import Escenario, Sesion
from app.domain.recursos import Recurso
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
from app.validator.estado import EstadoHorario

#: 1=lunes … 5=viernes (DOMAIN.md). Se repite acá y no se importa de
#: `app.importer.coercion`: `app.importer` ya importa `app.validator`.
NOMBRE_DIA = ("", "lunes", "martes", "miércoles", "jueves", "viernes")

#: Clave de una franja concreta de la versión.
_Franja = tuple[uuid.UUID, int, uuid.UUID]


def validar(
    estado: EstadoHorario,
    escenario: Escenario | uuid.UUID | None = None,
    al_publicar: bool = False,
) -> list[Conflicto]:
    """Todos los conflictos del horario, ordenados de forma determinista.

    Args:
        estado: foto del horario en dataclasses. Las sesiones sin asignación o sin
            recurso conocido se omiten en las reglas que dependen de ese dato: el
            validador nunca lanza sobre un estado parcial.
        escenario: escenario activo (objeto o id). Solo se aplican los
            `escenario_cambio` de ese escenario. `None` = estado base.
        al_publicar: `False` mientras se edita, `True` al publicar. Solo cambia la
            gravedad de `MALLA_INCUMPLIDA`.

    Returns:
        Lista de conflictos; vacía si el horario está limpio.
    """
    bloques = {bloque.id: bloque for bloque in estado.bloques}
    cursos = {curso.id: curso for curso in estado.cursos}
    docentes = {docente.id: docente for docente in estado.docentes}
    asignaturas = {asignatura.id: asignatura for asignatura in estado.asignaturas}
    recursos = {recurso.id: recurso for recurso in estado.recursos}
    asignaciones = {asignacion.id: asignacion for asignacion in estado.asignaciones}
    aptitudes = {(aptitud.docente_id, aptitud.asignatura_id) for aptitud in estado.aptitudes}

    conflictos: list[Conflicto] = []
    conflictos.extend(_choques(estado.sesiones, bloques, cursos, docentes, recursos))
    conflictos.extend(_bloques_no_clase(estado.sesiones, bloques, cursos))
    conflictos.extend(
        _no_disponibles(
            estado.sesiones,
            _franjas_bloqueadas(estado, _id_escenario(escenario)),
            bloques,
            docentes,
        )
    )
    conflictos.extend(
        _no_habilitados(estado.sesiones, asignaciones, asignaturas, aptitudes, docentes, cursos)
    )
    conflictos.extend(_recursos(estado.sesiones, asignaciones, asignaturas, cursos, recursos))
    conflictos.extend(_sobrecarga(estado.sesiones, docentes))
    conflictos.extend(
        _malla(estado.sesiones, estado.asignaciones, asignaturas, cursos, al_publicar)
    )
    conflictos.extend(_pesadas_consecutivas(estado, asignaciones, asignaturas, cursos))
    conflictos.sort(key=lambda conflicto: (conflicto.codigo, _clave(conflicto.sesion_ids)))
    return conflictos


def _clave(sesion_ids: tuple[uuid.UUID, ...]) -> tuple[str, ...]:
    return tuple(str(sesion_id) for sesion_id in sesion_ids)


def _id_escenario(escenario: Escenario | uuid.UUID | None) -> uuid.UUID | None:
    if escenario is None:
        return None
    return escenario if isinstance(escenario, uuid.UUID) else escenario.id


def _franjas_bloqueadas(
    estado: EstadoHorario, escenario_id: uuid.UUID | None
) -> set[tuple[uuid.UUID, int, uuid.UUID]]:
    """Franjas en las que el docente no está disponible, con el overlay aplicado.

    Base: `disponibilidad_bloqueo` (estado real). Overlay: `escenario_cambio` del
    escenario activo — `disponible_nuevo=true` libera, `false` bloquea (D-005).
    """
    bloqueadas = {
        (bloqueo.docente_id, bloqueo.dia, bloqueo.bloque_id) for bloqueo in estado.bloqueos
    }
    if escenario_id is None:
        return bloqueadas
    for cambio in estado.escenario_cambios:
        if cambio.escenario_id != escenario_id:
            continue
        franja = (cambio.docente_id, cambio.dia, cambio.bloque_id)
        if cambio.disponible_nuevo:
            bloqueadas.discard(franja)
        else:
            bloqueadas.add(franja)
    return bloqueadas


def _dia(dia: int) -> str:
    return NOMBRE_DIA[dia] if 0 < dia < len(NOMBRE_DIA) else f"día {dia}"


def _bloque(bloques: dict[uuid.UUID, Bloque], bloque_id: uuid.UUID) -> str:
    bloque = bloques.get(bloque_id)
    return bloque.codigo if bloque is not None else "desconocido"


def _curso(cursos: dict[uuid.UUID, Curso], curso_id: uuid.UUID) -> str:
    curso = cursos.get(curso_id)
    return curso.codigo if curso is not None else "curso desconocido"


def _docente(docentes: dict[uuid.UUID, Docente], docente_id: uuid.UUID) -> str:
    docente = docentes.get(docente_id)
    if docente is None:
        return "docente desconocido"
    return f"{docente.codigo} ({docente.nombre})"


def _choques(
    sesiones: tuple[Sesion, ...],
    bloques: dict[uuid.UUID, Bloque],
    cursos: dict[uuid.UUID, Curso],
    docentes: dict[uuid.UUID, Docente],
    recursos: dict[uuid.UUID, Recurso],
) -> list[Conflicto]:
    """Docente, curso o recurso en dos sesiones del mismo (versión, día, bloque)."""
    por_docente: dict[tuple[uuid.UUID, int, uuid.UUID, uuid.UUID], list[Sesion]] = defaultdict(
        list
    )
    por_curso: dict[tuple[uuid.UUID, int, uuid.UUID, uuid.UUID], list[Sesion]] = defaultdict(list)
    por_recurso: dict[tuple[uuid.UUID, int, uuid.UUID, uuid.UUID], list[Sesion]] = defaultdict(list)

    for sesion in sesiones:
        version, dia, bloque_id = sesion.horario_version_id, sesion.dia, sesion.bloque_id
        por_docente[(version, dia, bloque_id, sesion.docente_id)].append(sesion)
        por_curso[(version, dia, bloque_id, sesion.curso_id)].append(sesion)
        if sesion.recurso_id is not None:
            por_recurso[(version, dia, bloque_id, sesion.recurso_id)].append(sesion)

    conflictos: list[Conflicto] = []
    for (_, dia, bloque_id, docente_id), grupo in por_docente.items():
        if len(grupo) < 2:
            continue
        conflictos.append(
            Conflicto(
                codigo=DOCENTE_DOBLE,
                gravedad=Gravedad.error,
                mensaje=(
                    f"{_docente(docentes, docente_id)} tiene {len(grupo)} clases a la vez "
                    f"el {_dia(dia)} en el bloque {_bloque(bloques, bloque_id)}."
                ),
                sesion_ids=_ids(grupo),
            )
        )
    for (_, dia, bloque_id, curso_id), grupo in por_curso.items():
        if len(grupo) < 2:
            continue
        conflictos.append(
            Conflicto(
                codigo=CURSO_DOBLE,
                gravedad=Gravedad.error,
                mensaje=(
                    f"{_curso(cursos, curso_id)} tiene {len(grupo)} clases a la vez "
                    f"el {_dia(dia)} en el bloque {_bloque(bloques, bloque_id)}."
                ),
                sesion_ids=_ids(grupo),
            )
        )
    for (_, dia, bloque_id, recurso_id), grupo in por_recurso.items():
        if len(grupo) < 2:
            continue
        recurso = recursos.get(recurso_id)
        nombre = recurso.nombre if recurso is not None else "recurso desconocido"
        conflictos.append(
            Conflicto(
                codigo=RECURSO_DOBLE,
                gravedad=Gravedad.error,
                mensaje=(
                    f"{nombre} está asignado a {len(grupo)} clases a la vez "
                    f"el {_dia(dia)} en el bloque {_bloque(bloques, bloque_id)}."
                ),
                sesion_ids=_ids(grupo),
            )
        )
    return conflictos


def _ids(sesiones: list[Sesion]) -> tuple[uuid.UUID, ...]:
    return tuple(sesion.id for sesion in sesiones)


def _bloques_no_clase(
    sesiones: tuple[Sesion, ...],
    bloques: dict[uuid.UUID, Bloque],
    cursos: dict[uuid.UUID, Curso],
) -> list[Conflicto]:
    """Ninguna sesión puede vivir en descanso, almuerzo o en un bloque inexistente."""
    conflictos: list[Conflicto] = []
    for sesion in sesiones:
        bloque = bloques.get(sesion.bloque_id)
        if bloque is not None and bloque.tipo == TipoBloque.clase:
            continue
        curso = _curso(cursos, sesion.curso_id)
        if bloque is None:
            mensaje = f"{curso} tiene una sesión en un bloque que no está en el catálogo."
        else:
            mensaje = (
                f"{curso} tiene una sesión en el bloque {bloque.codigo}, "
                f"que es {bloque.tipo} y no de clase."
            )
        conflictos.append(
            Conflicto(
                codigo=BLOQUE_NO_CLASE,
                gravedad=Gravedad.error,
                mensaje=mensaje,
                sesion_ids=(sesion.id,),
            )
        )
    return conflictos


def _no_disponibles(
    sesiones: tuple[Sesion, ...],
    bloqueadas: set[tuple[uuid.UUID, int, uuid.UUID]],
    bloques: dict[uuid.UUID, Bloque],
    docentes: dict[uuid.UUID, Docente],
) -> list[Conflicto]:
    conflictos: list[Conflicto] = []
    for sesion in sesiones:
        if (sesion.docente_id, sesion.dia, sesion.bloque_id) not in bloqueadas:
            continue
        conflictos.append(
            Conflicto(
                codigo=DOCENTE_NO_DISPONIBLE,
                gravedad=Gravedad.error,
                mensaje=(
                    f"{_docente(docentes, sesion.docente_id)} no está disponible "
                    f"el {_dia(sesion.dia)} en el bloque {_bloque(bloques, sesion.bloque_id)}."
                ),
                sesion_ids=(sesion.id,),
            )
        )
    return conflictos


def _no_habilitados(
    sesiones: tuple[Sesion, ...],
    asignaciones: dict[uuid.UUID, AsignacionCarga],
    asignaturas: dict[uuid.UUID, Asignatura],
    aptitudes: set[tuple[uuid.UUID, uuid.UUID]],
    docentes: dict[uuid.UUID, Docente],
    cursos: dict[uuid.UUID, Curso],
) -> list[Conflicto]:
    conflictos: list[Conflicto] = []
    for sesion in sesiones:
        asignacion = asignaciones.get(sesion.asignacion_carga_id)
        if asignacion is None:
            continue
        if (sesion.docente_id, asignacion.asignatura_id) in aptitudes:
            continue
        asignatura = asignaturas.get(asignacion.asignatura_id)
        nombre = asignatura.nombre if asignatura is not None else "la asignatura"
        conflictos.append(
            Conflicto(
                codigo=DOCENTE_NO_HABILITADO,
                gravedad=Gravedad.error,
                mensaje=(
                    f"{_docente(docentes, sesion.docente_id)} no está habilitado para "
                    f"{nombre} en {_curso(cursos, sesion.curso_id)}."
                ),
                sesion_ids=(sesion.id,),
            )
        )
    return conflictos


def _recursos(
    sesiones: tuple[Sesion, ...],
    asignaciones: dict[uuid.UUID, AsignacionCarga],
    asignaturas: dict[uuid.UUID, Asignatura],
    cursos: dict[uuid.UUID, Curso],
    recursos: dict[uuid.UUID, Recurso],
) -> list[Conflicto]:
    """El recurso debe ser del tipo pedido y entrar el curso (DOMAIN.md)."""
    conflictos: list[Conflicto] = []
    for sesion in sesiones:
        if sesion.recurso_id is None:
            continue
        recurso = recursos.get(sesion.recurso_id)
        asignacion = asignaciones.get(sesion.asignacion_carga_id)
        if recurso is None or asignacion is None:
            continue
        curso = cursos.get(sesion.curso_id)
        etiqueta = _curso(cursos, sesion.curso_id)
        asignatura = asignaturas.get(asignacion.asignatura_id)
        nombre_asignatura = asignatura.nombre if asignatura is not None else "la asignatura"
        if recurso.tipo_recurso != asignacion.tipo_recurso_requerido:
            conflictos.append(
                Conflicto(
                    codigo=RECURSO_TIPO_INCORRECTO,
                    gravedad=Gravedad.error,
                    mensaje=(
                        f"{recurso.nombre} es de tipo {recurso.tipo_recurso} y {nombre_asignatura} "
                        f"de {etiqueta} necesita {asignacion.tipo_recurso_requerido}."
                    ),
                    sesion_ids=(sesion.id,),
                )
            )
        if curso is not None and recurso.capacidad < curso.estudiantes:
            conflictos.append(
                Conflicto(
                    codigo=RECURSO_CAPACIDAD,
                    gravedad=Gravedad.error,
                    mensaje=(
                        f"{recurso.nombre} tiene capacidad {recurso.capacidad} y "
                        f"{curso.codigo} necesita {curso.estudiantes}."
                    ),
                    sesion_ids=(sesion.id,),
                )
            )
    return conflictos


def _sobrecarga(
    sesiones: tuple[Sesion, ...], docentes: dict[uuid.UUID, Docente]
) -> list[Conflicto]:
    """Sesiones colocadas del docente por encima de su máximo semanal."""
    por_docente: dict[uuid.UUID, list[Sesion]] = defaultdict(list)
    for sesion in sesiones:
        por_docente[sesion.docente_id].append(sesion)

    conflictos: list[Conflicto] = []
    for docente_id, grupo in por_docente.items():
        docente = docentes.get(docente_id)
        if docente is None or len(grupo) <= docente.max_sesiones_semana:
            continue
        conflictos.append(
            Conflicto(
                codigo=DOCENTE_SOBRECARGA,
                gravedad=Gravedad.error,
                mensaje=(
                    f"{docente.codigo} ({docente.nombre}) tiene {len(grupo)} sesiones "
                    f"y su máximo semanal es {docente.max_sesiones_semana}."
                ),
                sesion_ids=_ids(grupo),
            )
        )
    return conflictos


def _malla(
    sesiones: tuple[Sesion, ...],
    asignaciones: tuple[AsignacionCarga, ...],
    asignaturas: dict[uuid.UUID, Asignatura],
    cursos: dict[uuid.UUID, Curso],
    al_publicar: bool,
) -> list[Conflicto]:
    """Sesiones colocadas ≠ `sesiones_semana`. Gravedad según `al_publicar` (D-011)."""
    colocadas: dict[uuid.UUID, list[Sesion]] = defaultdict(list)
    for sesion in sesiones:
        colocadas[sesion.asignacion_carga_id].append(sesion)

    gravedad = Gravedad.error if al_publicar else Gravedad.advertencia
    conflictos: list[Conflicto] = []
    for asignacion in asignaciones:
        grupo = colocadas.get(asignacion.id, [])
        if len(grupo) == asignacion.sesiones_semana:
            continue
        asignatura = asignaturas.get(asignacion.asignatura_id)
        nombre = asignatura.nombre if asignatura is not None else "Asignatura"
        conflictos.append(
            Conflicto(
                codigo=MALLA_INCUMPLIDA,
                gravedad=gravedad,
                mensaje=(
                    f"{nombre} ({_curso(cursos, asignacion.curso_id)}): "
                    f"{len(grupo)} de {asignacion.sesiones_semana} sesiones colocadas."
                ),
                sesion_ids=_ids(grupo),
            )
        )
    return conflictos


def _asignatura_pesada(
    sesion: Sesion,
    asignaciones: dict[uuid.UUID, AsignacionCarga],
    asignaturas: dict[uuid.UUID, Asignatura],
) -> str | None:
    asignacion = asignaciones.get(sesion.asignacion_carga_id)
    if asignacion is None:
        return None
    asignatura = asignaturas.get(asignacion.asignatura_id)
    if asignatura is None or not asignatura.es_pesada:
        return None
    return asignatura.nombre


def _pesadas_consecutivas(
    estado: EstadoHorario,
    asignaciones: dict[uuid.UUID, AsignacionCarga],
    asignaturas: dict[uuid.UUID, Asignatura],
    cursos: dict[uuid.UUID, Curso],
) -> list[Conflicto]:
    """Dos bloques de clase consecutivos con asignaturas pesadas. Regla blanda (D-006).

    "Sin descanso/almuerzo entre medio" sale gratis: si un bloque no-clase está en
    el medio, los `orden` de clase dejan de ser consecutivos. Como el Excel no trae
    descansos, son los 5 pares de cada día por curso.
    """
    clase = sorted(
        (bloque for bloque in estado.bloques if bloque.tipo == TipoBloque.clase),
        key=lambda bloque: bloque.orden,
    )
    pares = [
        (primero, segundo)
        for primero, segundo in zip(clase, clase[1:], strict=False)
        if segundo.orden == primero.orden + 1
    ]
    if not pares:
        return []

    en_franja: dict[tuple[uuid.UUID, int, uuid.UUID], list[Sesion]] = defaultdict(list)
    for sesion in estado.sesiones:
        en_franja[(sesion.curso_id, sesion.dia, sesion.bloque_id)].append(sesion)

    dias = sorted({sesion.dia for sesion in estado.sesiones})
    conflictos: list[Conflicto] = []
    for curso_id in sorted({sesion.curso_id for sesion in estado.sesiones}, key=str):
        for dia in dias:
            for primero, segundo in pares:
                antes = _primera(en_franja.get((curso_id, dia, primero.id)))
                despues = _primera(en_franja.get((curso_id, dia, segundo.id)))
                if antes is None or despues is None:
                    continue
                nombre_antes = _asignatura_pesada(antes, asignaciones, asignaturas)
                nombre_despues = _asignatura_pesada(despues, asignaciones, asignaturas)
                if nombre_antes is None or nombre_despues is None:
                    continue
                conflictos.append(
                    Conflicto(
                        codigo=ASIGNATURA_PESADA_CONSECUTIVA,
                        gravedad=Gravedad.advertencia,
                        mensaje=(
                            f"{_curso(cursos, curso_id)}: {nombre_antes} y {nombre_despues} "
                            f"quedan seguidas el {_dia(dia)} (bloques {primero.codigo} y "
                            f"{segundo.codigo}) sin descanso entre medio."
                        ),
                        sesion_ids=(antes.id, despues.id),
                    )
                )
    return conflictos


def _primera(sesiones: list[Sesion] | None) -> Sesion | None:
    if not sesiones:
        return None
    return min(sesiones, key=lambda sesion: str(sesion.id))
