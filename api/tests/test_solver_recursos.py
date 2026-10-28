"""Asignación de aulas y reglas del modelo que el golden no aísla.

Casos mínimos y sintéticos: el archivo real no tiene recursos restrictivos (4 salones
por tipo para 4 cursos), así que la rama "no hay aula libre" no se puede provocar con
la demo. Documentado en `DOMAIN.md`: los salones nunca son restrictivos ahí.
"""

from app.domain.carga import AsignacionCarga
from app.domain.catalogo import Docente
from app.solver import RECURSO_NO_DISPONIBLE, asignar_recursos, resolver
from app.solver.resultado import EstadoResultado
from app.validator import DOCENTE_SOBRECARGA
from tests.factories import HorarioEnMemoria


def _laboratorio(h: HorarioEnMemoria, curso, docente, codigo: str = "LAB") -> AsignacionCarga:
    asignatura = h.asignatura(codigo)
    h.habilitar(docente, asignatura)
    return h.asignacion(curso, asignatura, docente, tipo_recurso="LAB_CIENCIAS")


def test_aula_titular_gana_el_desempate() -> None:
    h = HorarioEnMemoria()
    curso = h.curso("6A")
    docente = h.docente("D1")
    carga = _laboratorio(h, curso, docente)
    titular = h.recurso("Aula 6A", tipo="LAB_CIENCIAS", capacidad=30, curso_titular=curso)
    h.recurso("Aula 9Z", tipo="LAB_CIENCIAS", capacidad=40)
    bloque = h.bloque("B1")
    sesion = h.colocar(carga, 1, bloque)

    plan, diagnosticos = asignar_recursos(h.estado(), (sesion,))

    assert plan[0].recurso_id == titular.id
    assert diagnosticos == ()


def test_sin_aula_libre_devuelve_diagnostico_y_no_un_recurso_invalido() -> None:
    h = HorarioEnMemoria()
    curso_a, curso_b = h.curso("6A"), h.curso("6B")
    docente_a, docente_b = h.docente("D1"), h.docente("D2")
    carga_a = _laboratorio(h, curso_a, docente_a, "Naturales")
    carga_b = _laboratorio(h, curso_b, docente_b, "Química")
    laboratorio = h.recurso("Laboratorio 1", tipo="LAB_CIENCIAS", capacidad=32)
    bloque = h.bloque("B1")
    primera = h.colocar(carga_a, 1, bloque)
    segunda = h.colocar(carga_b, 1, bloque)

    plan, diagnosticos = asignar_recursos(h.estado(), (primera, segunda))

    con_aula = [sesion for sesion in plan if sesion.recurso_id == laboratorio.id]
    sin_aula = [sesion for sesion in plan if sesion.recurso_id is None]
    assert len(con_aula) == 1
    assert len(sin_aula) == 1
    assert [diagnostico.codigo for diagnostico in diagnosticos] == [RECURSO_NO_DISPONIBLE]
    assert "LAB_CIENCIAS" in diagnosticos[0].mensaje


def test_aula_sin_capacidad_no_se_usa() -> None:
    h = HorarioEnMemoria()
    curso = h.curso("6A", estudiantes=30)
    docente = h.docente("D1")
    carga = _laboratorio(h, curso, docente)
    h.recurso("Laboratorio chico", tipo="LAB_CIENCIAS", capacidad=20)
    bloque = h.bloque("B1")
    sesion = h.colocar(carga, 1, bloque)

    plan, diagnosticos = asignar_recursos(h.estado(), (sesion,))

    assert plan[0].recurso_id is None
    assert [diagnostico.codigo for diagnostico in diagnosticos] == [RECURSO_NO_DISPONIBLE]


def test_sobrecarga_del_docente_es_infactible_con_causa() -> None:
    h = HorarioEnMemoria()
    curso = h.curso("6A")
    docente = h.docente("D1", maximo=3)
    for nombre in ("Matemáticas", "Lenguaje"):
        h.bloque(f"B{len(h.bloques) + 1}")
        asignatura = h.asignatura(nombre)
        h.habilitar(docente, asignatura)
        h.asignacion(curso, asignatura, docente, sesiones=4)
    estado = h.estado()

    resultado = resolver(estado, modo_docente="habilitados")

    assert resultado.estado is EstadoResultado.INFACTIBLE
    assert resultado.sesiones == ()
    sobrecargas = [
        diagnostico
        for diagnostico in resultado.diagnostico
        if diagnostico.codigo == DOCENTE_SOBRECARGA
    ]
    assert sobrecargas and sobrecargas[0].docente_codigo == "D1"


def test_modo_habilitados_usa_la_aptitud_y_no_solo_al_principal() -> None:
    h = HorarioEnMemoria()
    curso = h.curso("6A")
    principal = h.docente("D1")
    habilitado = h.docente("D2")
    h.bloque("B1")
    matematicas = h.asignatura("Matemáticas")
    h.habilitar(habilitado, matematicas)
    h.asignacion(curso, matematicas, principal, sesiones=1)
    estado = h.estado()

    principal_fijo = resolver(estado, modo_docente="principal")
    habilitados = resolver(estado, modo_docente="habilitados")

    assert [sesion.docente_id for sesion in principal_fijo.sesiones] == [principal.id]
    assert [sesion.docente_id for sesion in habilitados.sesiones] == [habilitado.id]


def test_docente_inactivo_no_recibe_sesiones() -> None:
    h = HorarioEnMemoria()
    curso = h.curso("6A")
    h.bloque("B1")
    matematicas = h.asignatura("Matemáticas")
    inactivo = Docente(codigo="D9", nombre="Docente 9", max_sesiones_semana=24, activo=False)
    h.docentes.append(inactivo)
    activo = h.docente("D1")
    h.habilitar(inactivo, matematicas)
    h.habilitar(activo, matematicas)
    h.asignacion(curso, matematicas, inactivo, sesiones=1)
    estado = h.estado()

    resultado = resolver(estado, modo_docente="habilitados")

    assert resultado.sesiones
    assert all(sesion.docente_id == activo.id for sesion in resultado.sesiones)
