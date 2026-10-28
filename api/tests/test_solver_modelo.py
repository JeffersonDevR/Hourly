"""Reglas del modelo que el golden no aísla: malla parcial y regeneración por curso.

El caso real (30 sesiones para 30 franjas) lo cubre `test_solver_golden.py`. Acá se
prueban las dos ramas que el archivo de la demo nunca ejercita: un curso con demanda
menor que la grilla y `solo_curso_id` con y sin `limpiar` (D-008).
"""

from dataclasses import replace

from app.domain.enums import Gravedad
from app.solver import EstadoResultado, resolver
from app.validator import validar
from tests.factories import HorarioEnMemoria
from tests.solverutil import buscar, estado_demo


def _errores(estado) -> list:
    return [c for c in validar(estado) if c.gravedad == Gravedad.error]


def test_malla_parcial_no_se_vuelve_infactible() -> None:
    """Demanda < franjas: el curso deja huecos, no rompe el modelo."""
    h = HorarioEnMemoria()
    curso = h.curso("6A")
    h.bloque("B1")
    docente = h.docente("D1")
    matematicas = h.asignatura("Matemáticas")
    h.habilitar(docente, matematicas)
    h.recurso("Aula 6A", capacidad=30, curso_titular=curso)
    h.asignacion(curso, matematicas, docente, sesiones=3)
    estado = h.estado()

    resultado = resolver(estado, modo_docente="habilitados")

    assert resultado.estado in (EstadoResultado.OPTIMO, EstadoResultado.FACTIBLE)
    assert len(resultado.sesiones) == 3
    assert _errores(replace(estado, sesiones=resultado.sesiones)) == []


def test_solo_curso_id_con_limpiar_regenera_ese_curso_y_nada_mas() -> None:
    """Regenerar un curso no puede borrar el trabajo de los demás (D-008)."""
    estado = estado_demo()
    completo = resolver(estado, modo_docente="habilitados")
    con_plan = replace(estado, sesiones=completo.sesiones)
    curso = buscar(estado.cursos, "7A")

    regenerado = resolver(
        con_plan, modo_docente="habilitados", solo_curso_id=curso.id, limpiar=True
    )

    assert len(regenerado.sesiones) == 120
    ajenas_antes = [sesion for sesion in completo.sesiones if sesion.curso_id != curso.id]
    ajenas_despues = [sesion for sesion in regenerado.sesiones if sesion.curso_id != curso.id]
    assert [sesion.id for sesion in ajenas_despues] == [sesion.id for sesion in ajenas_antes]
    assert _errores(replace(estado, sesiones=regenerado.sesiones)) == []


def test_solo_curso_id_sin_limpiar_respeta_las_sesiones_existentes() -> None:
    """Sin `limpiar`, las sesiones del curso son `fijas`: no se mueven."""
    estado = estado_demo()
    completo = resolver(estado, modo_docente="habilitados")
    con_plan = replace(estado, sesiones=completo.sesiones)
    curso = buscar(estado.cursos, "7A")

    resultado = resolver(con_plan, modo_docente="habilitados", solo_curso_id=curso.id)

    propias_antes = {sesion.id for sesion in completo.sesiones if sesion.curso_id == curso.id}
    propias_despues = {
        sesion.id for sesion in resultado.sesiones if sesion.curso_id == curso.id
    }
    assert propias_despues == propias_antes
