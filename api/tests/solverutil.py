"""Estado de la demo armado desde el Excel real, para los golden del solver.

No hay datos inventados: se lee `data/Datos_prueba_Gnosoft.xlsx` con el importador de
la fase 2 (`leer_libro` + `analizar_libro`) y se hidrata `EstadoHorario`. Los UUID son
`uuid5` de las claves naturales, así que dos corridas del test dan el mismo grafo.

Se usa el importador y no la DB porque el estado completo (incluidos recursos, que
`diagnosticar_carga` no necesita) cabe en una función pura: sin alembic, sin sesión
SQLAlchemy y sin tocar `hourly.db`.
"""

import uuid
from collections.abc import Collection
from functools import lru_cache
from pathlib import Path

from app.domain.carga import AsignacionCarga, DisponibilidadBloqueo
from app.domain.catalogo import Aptitud, Asignatura, Bloque, Curso, Docente
from app.domain.enums import OrigenBloqueo
from app.domain.horario import Escenario, EscenarioCambio, Sesion
from app.domain.recursos import Recurso
from app.importer.analisis import analizar_libro
from app.importer.lectura import leer_libro
from app.importer.modelos import PreviewImportacion
from app.validator.estado import EstadoHorario

DATOS = Path(__file__).resolve().parents[2] / "data" / "Datos_prueba_Gnosoft.xlsx"

_NS = uuid.uuid5(uuid.NAMESPACE_URL, "hourly/solver/demo")

#: Id del escenario "D2 sin clase el martes" que trae la hoja Cambio.
ESCENARIO_ID = uuid.uuid5(_NS, "escenario:importado")
#: Id de la versión de la demo: no hay DB, pero `sesion.horario_version_id` lo exige.
VERSION_ID = uuid.uuid5(_NS, "version:1")


def id_de(*partes: str) -> uuid.UUID:
    return uuid.uuid5(_NS, ":".join(partes))


@lru_cache(maxsize=1)
def preview_demo() -> PreviewImportacion:
    """Análisis del archivo real, una sola vez por proceso."""
    return analizar_libro(leer_libro(DATOS.read_bytes()), archivo_nombre=DATOS.name)


def estado_demo(pesadas: Collection[str] = ()) -> EstadoHorario:
    """`EstadoHorario` completo del archivo real.

    Args:
        pesadas: nombres de asignatura que se marcan `es_pesada=True`. El Excel no
            trae la columna (D-006), así que la regla blanda solo se puede medir
            marcando asignaturas explícitamente en el test.
    """
    preview = preview_demo()

    cursos = tuple(
        Curso(
            codigo=curso.codigo,
            nombre=curso.nombre,
            grado_id=id_de("grado", str(curso.grado)),
            estudiantes=curso.estudiantes,
            id=id_de("curso", curso.codigo),
        )
        for curso in preview.cursos
    )
    bloques = tuple(
        Bloque(
            codigo=bloque.codigo,
            orden=bloque.orden,
            inicio=bloque.inicio,
            fin=bloque.fin,
            duracion_min=bloque.duracion_min,
            tipo=bloque.tipo,
            id=id_de("bloque", bloque.codigo),
        )
        for bloque in preview.bloques
    )
    docentes = tuple(
        Docente(
            codigo=docente.codigo,
            nombre=docente.nombre,
            max_sesiones_semana=docente.max_sesiones_semana,
            id=id_de("docente", docente.codigo),
        )
        for docente in preview.docentes
    )
    asignaturas = tuple(
        Asignatura(
            nombre=asignatura.nombre,
            color=asignatura.color,
            es_pesada=asignatura.nombre in pesadas,
            id=id_de("asignatura", asignatura.nombre),
        )
        for asignatura in preview.asignaturas
    )
    aptitudes = tuple(
        Aptitud(
            docente_id=id_de("docente", aptitud.docente),
            asignatura_id=id_de("asignatura", aptitud.asignatura),
        )
        for aptitud in preview.aptitudes
    )
    asignaciones = tuple(
        AsignacionCarga(
            curso_id=id_de("curso", asignacion.curso),
            asignatura_id=id_de("asignatura", asignacion.asignatura),
            docente_principal_id=id_de("docente", asignacion.docente_principal),
            sesiones_semana=asignacion.sesiones_semana,
            tipo_recurso_requerido=asignacion.tipo_recurso_requerido,
            id=id_de("carga", asignacion.curso, asignacion.asignatura),
        )
        for asignacion in preview.asignaciones
    )
    recursos = tuple(
        Recurso(
            codigo=recurso.codigo,
            nombre=recurso.nombre,
            tipo_recurso=recurso.tipo_recurso,
            capacidad=recurso.capacidad,
            curso_titular_id=(
                id_de("curso", recurso.curso_titular) if recurso.curso_titular else None
            ),
            id=id_de("recurso", recurso.codigo),
        )
        for recurso in preview.recursos
    )
    bloqueos = tuple(
        DisponibilidadBloqueo(
            docente_id=id_de("docente", bloqueo.docente),
            dia=bloqueo.dia,
            bloque_id=id_de("bloque", bloqueo.bloque),
            origen=OrigenBloqueo.personal,
            detalle="Importado de la hoja Disponibilidad",
        )
        for bloqueo in preview.bloqueos
    )
    cambios = tuple(
        EscenarioCambio(
            escenario_id=ESCENARIO_ID,
            docente_id=id_de("docente", cambio.docente),
            dia=cambio.dia,
            bloque_id=id_de("bloque", cambio.bloque),
            disponible_nuevo=cambio.disponible_nuevo,
            motivo=cambio.motivo,
        )
        for cambio in preview.escenario.cambios
    )

    return EstadoHorario(
        cursos=cursos,
        docentes=docentes,
        bloques=bloques,
        asignaturas=asignaturas,
        aptitudes=aptitudes,
        asignaciones=asignaciones,
        bloqueos=bloqueos,
        recursos=recursos,
        escenario_cambios=cambios,
        sesiones=(),
    )


def escenario_demo() -> Escenario:
    """El escenario "D2 sin clase el martes" con el id que usan los cambios."""
    return Escenario(
        nombre="D2 sin clase el martes",
        descripcion="Importado de la hoja Cambio.",
        id=ESCENARIO_ID,
    )


def buscar(coleccion, valor: str, atributo: str = "codigo"):
    """Primer elemento cuyo `atributo` coincide. Falla con un mensaje del dominio."""
    for elemento in coleccion:
        if getattr(elemento, atributo) == valor:
            return elemento
    raise AssertionError(f"No existe {atributo}={valor!r} en el estado de la demo")


def sesion_manual(
    estado: EstadoHorario,
    curso: str,
    asignatura: str,
    dia: int,
    bloque: str,
    docente: str | None = None,
) -> Sesion:
    """Sesión colocada a mano (sin aula) para probar `fijas` (D-008)."""
    curso_obj = buscar(estado.cursos, curso)
    asignatura_obj = buscar(estado.asignaturas, asignatura, "nombre")
    bloque_obj = buscar(estado.bloques, bloque)
    asignacion = next(
        carga
        for carga in estado.asignaciones
        if carga.curso_id == curso_obj.id and carga.asignatura_id == asignatura_obj.id
    )
    docente_id = (
        buscar(estado.docentes, docente).id
        if docente is not None
        else asignacion.docente_principal_id
    )
    return Sesion(
        horario_version_id=VERSION_ID,
        asignacion_carga_id=asignacion.id,
        curso_id=curso_obj.id,
        docente_id=docente_id,
        dia=dia,
        bloque_id=bloque_obj.id,
    )
