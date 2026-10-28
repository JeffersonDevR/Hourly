"""Paso 0 de D-003: el greedy propone, nunca aplica, y nunca propone algo inválido.

Los estados son sintéticos y mínimos (`HorarioEnMemoria`): el greedy es un algoritmo
sobre reglas, no sobre el archivo de la demo. El caso real está en el golden.
"""

import time
from dataclasses import replace

from app.domain.enums import Gravedad, TipoCambioPropuesta
from app.solver import PropuestaCambio, reparar_greedy
from app.validator import validar
from tests.factories import HorarioEnMemoria


def _errores(estado) -> list:
    return [c for c in validar(estado) if c.gravedad == Gravedad.error]


def _aplicar(estado, propuestas: tuple[PropuestaCambio, ...]):
    """Simula las propuestas sobre una copia: el test aplica, no el solver."""
    sesiones = list(estado.sesiones)
    for propuesta in propuestas:
        campos = {
            clave: valor
            for clave, valor in (
                ("dia", propuesta.dia),
                ("bloque_id", propuesta.bloque_id),
                ("docente_id", propuesta.docente_id),
                ("recurso_id", propuesta.recurso_id),
            )
            if valor is not None
        }
        sesiones = [
            replace(sesion, **campos) if sesion.id == propuesta.sesion_id else sesion
            for sesion in sesiones
        ]
    return replace(estado, sesiones=tuple(sesiones))


def _doble_reservado(h: HorarioEnMemoria, docente):
    """Dos cursos con el mismo docente en la misma franja."""
    curso_a, curso_b = h.curso("6A"), h.curso("6B")
    bloque = h.bloque("B1")
    matematicas = h.asignatura("Matemáticas")
    h.habilitar(docente, matematicas)
    primera = h.colocar(h.asignacion(curso_a, matematicas, docente), 1, bloque)
    segunda = h.colocar(h.asignacion(curso_b, matematicas, docente), 1, bloque)
    return primera, segunda


def test_greedy_mueve_la_sesion_a_una_franja_libre() -> None:
    h = HorarioEnMemoria()
    docente = h.docente("D1")
    primera, segunda = _doble_reservado(h, docente)
    estado = h.estado()
    assert len(_errores(estado)) == 1

    propuestas = reparar_greedy(estado)

    assert len(propuestas) == 1
    assert propuestas[0].tipo is TipoCambioPropuesta.mover_sesion
    assert propuestas[0].sesion_id == segunda.id  # 6B va después de 6A, es la que se mueve
    assert propuestas[0].dia is not None and propuestas[0].bloque_id is not None
    assert propuestas[0].sesion_id != primera.id
    assert _errores(_aplicar(estado, propuestas)) == []


def test_greedy_no_muta_el_estado_del_llamador() -> None:
    h = HorarioEnMemoria()
    primera, segunda = _doble_reservado(h, h.docente("D1"))
    estado = h.estado()

    reparar_greedy(estado)

    assert (primera, segunda) == estado.sesiones
    assert len(_errores(estado)) == 1


def test_greedy_cambia_docente_cuando_no_hay_franja_libre() -> None:
    """Un solo bloque por día: la única salida es otro docente con aptitud."""
    h = HorarioEnMemoria()
    curso_a, curso_b = h.curso("6A"), h.curso("6B")
    bloque = h.bloque("B1")
    docente_a, docente_b = h.docente("D1"), h.docente("D2")
    matematicas = h.asignatura("Matemáticas")
    h.habilitar(docente_a, matematicas)
    h.habilitar(docente_b, matematicas)
    for dia in range(1, 6):
        h.colocar(h.asignacion(curso_a, matematicas, docente_a), dia, bloque)
    for dia in range(1, 6):
        h.colocar(h.asignacion(curso_b, matematicas, docente_a), dia, bloque)
    estado = h.estado()
    assert len(_errores(estado)) == 5

    propuestas = reparar_greedy(estado)

    assert propuestas
    assert {propuesta.tipo for propuesta in propuestas} == {TipoCambioPropuesta.cambiar_docente}
    assert all(propuesta.docente_id == docente_b.id for propuesta in propuestas)
    assert _errores(_aplicar(estado, propuestas)) == []


def test_greedy_sin_franja_libre_no_inventa_un_movimiento() -> None:
    """Sin franja libre ni docente alternativo devuelve nada, no una propuesta inválida."""
    h = HorarioEnMemoria()
    curso = h.curso("6A")
    docente = h.docente("D1", maximo=24)
    bloque = h.bloque("B1")
    materias = [h.asignatura(nombre) for nombre in ("M1", "M2", "M3", "M4", "M5", "M6")]
    for asignatura in materias:
        h.habilitar(docente, asignatura)
    # Cinco franjas (5 días × el único bloque) y seis sesiones: una sobra.
    cargas = [h.asignacion(curso, asignatura, docente) for asignatura in materias]
    for dia, carga in zip(range(1, 6), cargas[:5], strict=True):
        h.colocar(carga, dia, bloque)
    h.colocar(cargas[5], 1, bloque)
    estado = h.estado()

    assert reparar_greedy(estado) == ()


def test_greedy_respeta_las_fijas() -> None:
    h = HorarioEnMemoria()
    primera, segunda = _doble_reservado(h, h.docente("D1"))
    estado = h.estado()

    assert reparar_greedy(estado, fijas=(primera, segunda)) == ()
    propuestas = reparar_greedy(estado, fijas=(segunda,))
    assert all(propuesta.sesion_id != segunda.id for propuesta in propuestas)


def test_greedy_cambia_el_recurso_por_tipo_y_capacidad() -> None:
    h = HorarioEnMemoria()
    curso = h.curso("6A")
    docente = h.docente("D1")
    bloque = h.bloque("B1")
    educacion_fisica = h.asignatura("Educación física")
    h.habilitar(docente, educacion_fisica)
    carga = h.asignacion(curso, educacion_fisica, docente, tipo_recurso="CANCHA")
    aula = h.recurso("Aula 6A", tipo="GENERAL", capacidad=30, curso_titular=curso)
    cancha = h.recurso("Cancha 1", tipo="CANCHA", capacidad=35)
    sesion = h.colocar(carga, 1, bloque, recurso=aula)
    estado = h.estado()
    assert _errores(estado)

    propuestas = reparar_greedy(estado)

    assert len(propuestas) == 1
    assert propuestas[0].tipo is TipoCambioPropuesta.cambiar_recurso
    assert propuestas[0].sesion_id == sesion.id
    assert propuestas[0].recurso_id == cancha.id


def test_greedy_120_sesiones_en_menos_de_100_ms() -> None:
    """D-003: determinista y por debajo de 100 ms incluso con la demo llena."""
    h = HorarioEnMemoria()
    bloques = [h.bloque(f"B{orden}") for orden in range(1, 7)]
    reemplazo = h.docente("D0")
    for curso_codigo in ("6A", "6B", "7A", "7B"):
        curso = h.curso(curso_codigo)
        cargas = []
        for indice, nombre in enumerate(
            ("Matemáticas", "Lenguaje", "Ciencias", "Sociales", "Artes")
        ):
            docente = h.docente(f"D-{curso_codigo}-{indice}")
            asignatura = h.asignatura(f"{nombre} {curso_codigo}")
            h.habilitar(docente, asignatura)
            h.habilitar(reemplazo, asignatura)
            cargas.append(h.asignacion(curso, asignatura, docente, sesiones=6))
        # 5 asignaciones × 6 sesiones = 30 franjas por curso.
        for dia in range(1, 6):
            for posicion, bloque in enumerate(bloques):
                h.colocar(cargas[(dia * len(bloques) + posicion) % len(cargas)], dia, bloque)
    estado = h.estado()
    assert len(estado.sesiones) == 120

    # Choque real de docente: una sesión de 7B pasa a tener el docente de 6A en su
    # misma franja. Sigue habiendo 120 sesiones.
    cursadas = {
        (sesion.curso_id, sesion.dia, sesion.bloque_id): sesion for sesion in estado.sesiones
    }
    curso_6a = next(curso for curso in h.cursos if curso.codigo == "6A")
    curso_7b = next(curso for curso in h.cursos if curso.codigo == "7B")
    victima = cursadas[(curso_7b.id, 1, bloques[0].id)]
    agresor = cursadas[(curso_6a.id, 1, bloques[0].id)]
    estado = replace(
        estado,
        sesiones=tuple(
            replace(sesion, docente_id=agresor.docente_id) if sesion.id == victima.id else sesion
            for sesion in estado.sesiones
        ),
    )
    assert "DOCENTE_DOBLE" in [conflicto.codigo for conflicto in validar(estado)]

    inicio = time.perf_counter()
    propuestas = reparar_greedy(estado)
    transcurrido = time.perf_counter() - inicio

    assert len(propuestas) == 1
    assert propuestas[0].docente_id == reemplazo.id
    assert transcurrido < 0.1, f"el greedy tardó {transcurrido * 1000:.1f} ms"
