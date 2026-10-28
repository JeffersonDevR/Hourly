"""Piezas compartidas del solver: franjas, bloques de clase y docentes permitidos.

Todo se deriva de `EstadoHorario` y es puro (`AGENTS.md`, regla 2): sin DB, sin HTTP
y sin `app.ai`. La regla del overlay de escenario (D-005) NO se reimplementa acá:
se importa del validador, que es la única fuente de verdad. Una segunda copia se
desincroniza en el primer cambio de semántica.
"""

import uuid
from collections import defaultdict
from collections.abc import Iterable

from app.domain.catalogo import Bloque, Docente
from app.domain.enums import ModoDocente, TipoBloque
from app.domain.horario import Escenario, Sesion
from app.validator.diagnostico import DIAS_SEMANA
from app.validator.estado import EstadoHorario
from app.validator.validacion import _franjas_bloqueadas

#: 1=lunes … 5=viernes (DOMAIN.md). El validador ya fija el ancho de la semana.
DIAS: tuple[int, ...] = tuple(range(1, DIAS_SEMANA + 1))

#: Namespace de los UUID sintéticos de las sesiones generadas: mismo input, mismos ids.
_NS_SESION = uuid.UUID("5f0e4a2c-0000-4000-8000-000000000004")

#: Franja concreta: (docente, día, bloque).
FranjaDocente = tuple[uuid.UUID, int, uuid.UUID]
#: Franja de un curso: (curso, día, bloque).
FranjaCurso = tuple[uuid.UUID, int, uuid.UUID]


def id_escenario(escenario: Escenario | uuid.UUID | None) -> uuid.UUID | None:
    """Acepta el objeto o el id, igual que `validar()`."""
    if escenario is None:
        return None
    return escenario if isinstance(escenario, uuid.UUID) else escenario.id


def franjas_bloqueadas(
    estado: EstadoHorario, escenario: Escenario | uuid.UUID | None
) -> set[FranjaDocente]:
    """Franjas donde el docente no está disponible, con el escenario ya aplicado.

    Delega en `app.validator.validacion._franjas_bloqueadas`: base de
    `disponibilidad_bloqueo` + overlay de `escenario_cambio` del escenario activo
    (D-005). El solver no puede tener su propia versión de esa regla.
    """
    return _franjas_bloqueadas(estado, id_escenario(escenario))


def bloques_clase(estado: EstadoHorario) -> tuple[Bloque, ...]:
    """Bloques que admiten sesiones, ordenados por `orden` (secuencia del día)."""
    return tuple(
        sorted(
            (bloque for bloque in estado.bloques if bloque.tipo == TipoBloque.clase),
            key=lambda bloque: (bloque.orden, bloque.codigo),
        )
    )


def pares_adyacentes(bloques: tuple[Bloque, ...]) -> tuple[tuple[Bloque, Bloque], ...]:
    """Pares consecutivos por `orden`, sin descanso/almuerzo en el medio.

    Si un bloque no-clase separa dos de clase, sus `orden` dejan de ser consecutivos
    y el par no aparece. Es la misma definición que usa `validar()` (D-006).
    """
    return tuple(
        (primero, segundo)
        for primero, segundo in zip(bloques, bloques[1:], strict=False)
        if segundo.orden == primero.orden + 1
    )


def franjas(bloques: tuple[Bloque, ...]) -> tuple[tuple[int, Bloque], ...]:
    """Todas las franjas de la semana en orden determinista: día y luego bloque."""
    return tuple((dia, bloque) for dia in DIAS for bloque in bloques)


def docentes_permitidos(
    estado: EstadoHorario, modo_docente: ModoDocente | str
) -> dict[uuid.UUID, tuple[Docente, ...]]:
    """Docentes que puede usar cada asignación según el modo.

    `principal`: solo `docente_principal_id`. `habilitados`: todos los docentes con
    `aptitud` para la asignatura. En ambos casos se filtra `activo=false`, que los
    saca del pool efectivo (`DOMAIN.md`). Orden determinista por código.
    """
    modo = ModoDocente(modo_docente)
    activos = {docente.id: docente for docente in estado.docentes if docente.activo}
    habilitados: dict[uuid.UUID, set[uuid.UUID]] = defaultdict(set)
    for aptitud in estado.aptitudes:
        habilitados[aptitud.asignatura_id].add(aptitud.docente_id)

    permitidos: dict[uuid.UUID, tuple[Docente, ...]] = {}
    for asignacion in estado.asignaciones:
        if modo is ModoDocente.principal:
            candidatos: Iterable[uuid.UUID] = (asignacion.docente_principal_id,)
        else:
            candidatos = habilitados.get(asignacion.asignatura_id, set())
        elegidos = [activos[docente_id] for docente_id in candidatos if docente_id in activos]
        elegidos.sort(key=lambda docente: docente.codigo)
        permitidos[asignacion.id] = tuple(elegidos)
    return permitidos


def carga_por_docente(sesiones: Iterable[Sesion]) -> dict[uuid.UUID, int]:
    """Sesiones colocadas por docente: la unidad de `max_sesiones_semana`."""
    carga: dict[uuid.UUID, int] = defaultdict(int)
    for sesion in sesiones:
        carga[sesion.docente_id] += 1
    return dict(carga)


def id_sesion(
    horario_version_id: uuid.UUID,
    asignacion_carga_id: uuid.UUID,
    dia: int,
    bloque_id: uuid.UUID,
) -> uuid.UUID:
    """ID estable de una sesión generada.

    Misma entrada, mismo id: los tests golden no dependen de un `uuid4`. Fase 5
    puede guardarlo tal cual en `sesion.id`.
    """
    return uuid.uuid5(
        _NS_SESION, f"{horario_version_id}:{asignacion_carga_id}:{dia}:{bloque_id}"
    )
