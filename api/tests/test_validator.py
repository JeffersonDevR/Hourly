"""Pruebas del validador puro: un caso por código de `DOMAIN.md` más los bordes.

Los estados se arman con dataclasses en memoria (`HorarioEnMemoria`), nunca por la
DB ni por el importador: `validar()` no conoce ninguna de las dos.

Excepción documentada a "nada de datos inventados": un bloque sintético
`tipo=descanso` se usa SOLO en los tests de `BLOQUE_NO_CLASE` y de
`ASIGNATURA_PESADA_CONSECUTIVA` (separador). El Excel real no trae descansos
(DOMAIN.md, trampa 3).
"""

import subprocess
import sys
import time
import uuid
from pathlib import Path

from app.domain.enums import Gravedad, TipoBloque
from app.validator import (
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
    validar,
)
from tests.factories import HorarioEnMemoria

#: Raíz de `api/`: ahí `import app` funciona sin instalar el paquete.
RUTA_API = Path(__file__).resolve().parents[1]


def _de(conflictos: list[Conflicto], codigo: str) -> list[Conflicto]:
    return [conflicto for conflicto in conflictos if conflicto.codigo == codigo]


def test_docente_doble() -> None:
    h = HorarioEnMemoria()
    curso_a, curso_b = h.curso("6A"), h.curso("6B")
    docente = h.docente("D1")
    bloque = h.bloque("B1")
    matematicas = h.asignatura("Matemáticas")
    h.habilitar(docente, matematicas)
    carga_a = h.asignacion(curso_a, matematicas, docente)
    carga_b = h.asignacion(curso_b, matematicas, docente)
    primera = h.colocar(carga_a, 1, bloque)
    segunda = h.colocar(carga_b, 1, bloque)

    conflictos = _de(validar(h.estado()), DOCENTE_DOBLE)

    assert len(conflictos) == 1
    assert conflictos[0].gravedad == Gravedad.error
    assert set(conflictos[0].sesion_ids) == {primera.id, segunda.id}
    assert "D1" in conflictos[0].mensaje


def test_docente_doble_en_dias_distintos_no_es_conflicto() -> None:
    h = HorarioEnMemoria()
    curso_a, curso_b = h.curso("6A"), h.curso("6B")
    docente = h.docente("D1")
    bloque = h.bloque("B1")
    matematicas = h.asignatura("Matemáticas")
    h.habilitar(docente, matematicas)
    h.colocar(h.asignacion(curso_a, matematicas, docente), 1, bloque)
    h.colocar(h.asignacion(curso_b, matematicas, docente), 2, bloque)

    assert validar(h.estado()) == []


def test_curso_doble() -> None:
    h = HorarioEnMemoria()
    curso = h.curso("6A")
    docente_a, docente_b = h.docente("D1"), h.docente("D2")
    bloque = h.bloque("B1")
    matematicas, lengua = h.asignatura("Matemáticas"), h.asignatura("Lengua")
    h.habilitar(docente_a, matematicas)
    h.habilitar(docente_b, lengua)
    primera = h.colocar(h.asignacion(curso, matematicas, docente_a), 1, bloque)
    segunda = h.colocar(h.asignacion(curso, lengua, docente_b), 1, bloque)

    conflictos = _de(validar(h.estado()), CURSO_DOBLE)

    assert len(conflictos) == 1
    assert conflictos[0].gravedad == Gravedad.error
    assert set(conflictos[0].sesion_ids) == {primera.id, segunda.id}
    assert "6A" in conflictos[0].mensaje


def test_mismo_bloque_en_cursos_distintos_no_es_conflicto() -> None:
    h = HorarioEnMemoria()
    curso_a, curso_b = h.curso("6A"), h.curso("6B")
    docente_a, docente_b = h.docente("D1"), h.docente("D2")
    bloque = h.bloque("B1")
    matematicas = h.asignatura("Matemáticas")
    h.habilitar(docente_a, matematicas)
    h.habilitar(docente_b, matematicas)
    h.colocar(h.asignacion(curso_a, matematicas, docente_a), 1, bloque)
    h.colocar(h.asignacion(curso_b, matematicas, docente_b), 1, bloque)

    assert validar(h.estado()) == []


def test_recurso_doble() -> None:
    h = HorarioEnMemoria()
    curso_a, curso_b = h.curso("6A"), h.curso("6B")
    docente_a, docente_b = h.docente("D1"), h.docente("D2")
    bloque = h.bloque("B1")
    matematicas = h.asignatura("Matemáticas")
    h.habilitar(docente_a, matematicas)
    h.habilitar(docente_b, matematicas)
    recurso = h.recurso("Aula 6A", capacidad=30)
    primera = h.colocar(h.asignacion(curso_a, matematicas, docente_a), 1, bloque, recurso=recurso)
    segunda = h.colocar(h.asignacion(curso_b, matematicas, docente_b), 1, bloque, recurso=recurso)

    conflictos = _de(validar(h.estado()), RECURSO_DOBLE)

    assert len(conflictos) == 1
    assert conflictos[0].gravedad == Gravedad.error
    assert set(conflictos[0].sesion_ids) == {primera.id, segunda.id}
    assert "Aula 6A" in conflictos[0].mensaje


def test_bloque_no_clase() -> None:
    # Excepción documentada: el descanso es sintético, el Excel no trae descansos.
    h = HorarioEnMemoria()
    curso = h.curso("6A")
    docente = h.docente("D1")
    descanso = h.bloque("B1", tipo=TipoBloque.descanso)
    matematicas = h.asignatura("Matemáticas")
    h.habilitar(docente, matematicas)
    sesion = h.colocar(h.asignacion(curso, matematicas, docente), 1, descanso)

    conflictos = _de(validar(h.estado()), BLOQUE_NO_CLASE)

    assert len(conflictos) == 1
    assert conflictos[0].gravedad == Gravedad.error
    assert conflictos[0].sesion_ids == (sesion.id,)
    assert "B1" in conflictos[0].mensaje


def test_docente_no_disponible() -> None:
    h = HorarioEnMemoria()
    curso = h.curso("6A")
    docente = h.docente("D1")
    bloque = h.bloque("B6")
    matematicas = h.asignatura("Matemáticas")
    h.habilitar(docente, matematicas)
    h.bloquear(docente, 5, bloque)
    sesion = h.colocar(h.asignacion(curso, matematicas, docente), 5, bloque)

    conflictos = _de(validar(h.estado()), DOCENTE_NO_DISPONIBLE)

    assert len(conflictos) == 1
    assert conflictos[0].gravedad == Gravedad.error
    assert conflictos[0].sesion_ids == (sesion.id,)
    assert "viernes" in conflictos[0].mensaje
    assert "B6" in conflictos[0].mensaje


def test_docente_no_habilitado() -> None:
    h = HorarioEnMemoria()
    curso = h.curso("6A")
    docente = h.docente("D1")
    bloque = h.bloque("B1")
    quimica = h.asignatura("Química")
    # Sin `h.habilitar(...)`: el docente no tiene aptitud para Química.
    sesion = h.colocar(h.asignacion(curso, quimica, docente), 1, bloque)

    conflictos = _de(validar(h.estado()), DOCENTE_NO_HABILITADO)

    assert len(conflictos) == 1
    assert conflictos[0].gravedad == Gravedad.error
    assert conflictos[0].sesion_ids == (sesion.id,)
    assert "Química" in conflictos[0].mensaje


def test_recurso_tipo_incorrecto() -> None:
    h = HorarioEnMemoria()
    curso = h.curso("6A")
    docente = h.docente("D1")
    bloque = h.bloque("B1")
    ciencias = h.asignatura("Ciencias Naturales")
    h.habilitar(docente, ciencias)
    carga = h.asignacion(curso, ciencias, docente, tipo_recurso="LAB_CIENCIAS")
    recurso = h.recurso("Aula 6A", tipo="GENERAL", capacidad=30)
    sesion = h.colocar(carga, 1, bloque, recurso=recurso)

    conflictos = _de(validar(h.estado()), RECURSO_TIPO_INCORRECTO)

    assert len(conflictos) == 1
    assert conflictos[0].gravedad == Gravedad.error
    assert conflictos[0].sesion_ids == (sesion.id,)
    assert "LAB_CIENCIAS" in conflictos[0].mensaje
    assert _de(validar(h.estado()), RECURSO_CAPACIDAD) == []


def test_recurso_capacidad() -> None:
    h = HorarioEnMemoria()
    curso = h.curso("6A", estudiantes=30)
    docente = h.docente("D1")
    bloque = h.bloque("B1")
    matematicas = h.asignatura("Matemáticas")
    h.habilitar(docente, matematicas)
    carga = h.asignacion(curso, matematicas, docente)
    recurso = h.recurso("Aula chica", capacidad=25)
    sesion = h.colocar(carga, 1, bloque, recurso=recurso)

    conflictos = _de(validar(h.estado()), RECURSO_CAPACIDAD)

    assert len(conflictos) == 1
    assert conflictos[0].gravedad == Gravedad.error
    assert conflictos[0].sesion_ids == (sesion.id,)
    assert "25" in conflictos[0].mensaje
    assert "30" in conflictos[0].mensaje


def test_recurso_con_capacidad_exacta_no_es_conflicto() -> None:
    h = HorarioEnMemoria()
    curso = h.curso("6A", estudiantes=30)
    docente = h.docente("D1")
    bloque = h.bloque("B1")
    matematicas = h.asignatura("Matemáticas")
    h.habilitar(docente, matematicas)
    carga = h.asignacion(curso, matematicas, docente)
    recurso = h.recurso("Aula 6A", capacidad=30)
    h.colocar(carga, 1, bloque, recurso=recurso)

    assert validar(h.estado()) == []


def test_docente_sobrecarga() -> None:
    h = HorarioEnMemoria()
    curso = h.curso("6A")
    docente = h.docente("D1", maximo=2)
    bloques = [h.bloque("B1"), h.bloque("B2"), h.bloque("B3")]
    matematicas = h.asignatura("Matemáticas")
    h.habilitar(docente, matematicas)
    carga = h.asignacion(curso, matematicas, docente, sesiones=3)
    sesiones = [h.colocar(carga, 1, bloque) for bloque in bloques]

    conflictos = _de(validar(h.estado()), DOCENTE_SOBRECARGA)

    assert len(conflictos) == 1
    assert conflictos[0].gravedad == Gravedad.error
    assert set(conflictos[0].sesion_ids) == {sesion.id for sesion in sesiones}
    assert "3 sesiones" in conflictos[0].mensaje
    assert "máximo semanal es 2" in conflictos[0].mensaje


def test_malla_incumplida_cambia_de_gravedad_al_publicar() -> None:
    h = HorarioEnMemoria()
    curso = h.curso("6A")
    docente = h.docente("D1")
    matematicas = h.asignatura("Matemáticas")
    h.habilitar(docente, matematicas)
    carga = h.asignacion(curso, matematicas, docente, sesiones=4)
    colocadas = [h.colocar(carga, 1, h.bloque(f"B{orden}")) for orden in (1, 2, 3)]
    estado = h.estado()

    en_edicion = _de(validar(estado), MALLA_INCUMPLIDA)
    al_publicar = _de(validar(estado, al_publicar=True), MALLA_INCUMPLIDA)

    assert len(en_edicion) == 1
    assert len(al_publicar) == 1
    assert en_edicion[0].gravedad == Gravedad.advertencia
    assert al_publicar[0].gravedad == Gravedad.error
    assert set(en_edicion[0].sesion_ids) == {sesion.id for sesion in colocadas}
    assert "3 de 4" in en_edicion[0].mensaje


def test_asignatura_pesada_consecutiva() -> None:
    h = HorarioEnMemoria()
    curso = h.curso("6A")
    docente_a, docente_b = h.docente("D1"), h.docente("D2")
    primero, segundo = h.bloque("B1"), h.bloque("B2")
    matematicas = h.asignatura("Matemáticas", pesada=True)
    ciencias = h.asignatura("Ciencias Naturales", pesada=True)
    h.habilitar(docente_a, matematicas)
    h.habilitar(docente_b, ciencias)
    sesion_a = h.colocar(h.asignacion(curso, matematicas, docente_a), 1, primero)
    sesion_b = h.colocar(h.asignacion(curso, ciencias, docente_b), 1, segundo)
    estado = h.estado()

    conflictos = _de(validar(estado), ASIGNATURA_PESADA_CONSECUTIVA)
    al_publicar = _de(validar(estado, al_publicar=True), ASIGNATURA_PESADA_CONSECUTIVA)

    assert len(conflictos) == 1
    assert conflictos[0].gravedad == Gravedad.advertencia
    assert conflictos[0].sesion_ids == (sesion_a.id, sesion_b.id)
    assert "Matemáticas" in conflictos[0].mensaje
    assert "Ciencias Naturales" in conflictos[0].mensaje
    # Regla blanda: publicar no la convierte en error (D-006).
    assert al_publicar[0].gravedad == Gravedad.advertencia


def test_pesada_junto_a_no_pesada_no_es_conflicto() -> None:
    h = HorarioEnMemoria()
    curso = h.curso("6A")
    docente_a, docente_b = h.docente("D1"), h.docente("D2")
    primero, segundo = h.bloque("B1"), h.bloque("B2")
    matematicas = h.asignatura("Matemáticas", pesada=True)
    arte = h.asignatura("Arte", pesada=False)
    h.habilitar(docente_a, matematicas)
    h.habilitar(docente_b, arte)
    h.colocar(h.asignacion(curso, matematicas, docente_a), 1, primero)
    h.colocar(h.asignacion(curso, arte, docente_b), 1, segundo)

    assert _de(validar(h.estado()), ASIGNATURA_PESADA_CONSECUTIVA) == []


def test_pesadas_separadas_por_un_descanso_no_es_conflicto() -> None:
    # Excepción documentada: el descanso es sintético, el Excel no trae descansos.
    h = HorarioEnMemoria()
    curso = h.curso("6A")
    docente_a, docente_b = h.docente("D1"), h.docente("D2")
    primero = h.bloque("B1")
    h.bloque("B2", tipo=TipoBloque.descanso)
    tercero = h.bloque("B3")
    matematicas = h.asignatura("Matemáticas", pesada=True)
    ciencias = h.asignatura("Ciencias Naturales", pesada=True)
    h.habilitar(docente_a, matematicas)
    h.habilitar(docente_b, ciencias)
    h.colocar(h.asignacion(curso, matematicas, docente_a), 1, primero)
    h.colocar(h.asignacion(curso, ciencias, docente_b), 1, tercero)

    assert _de(validar(h.estado()), ASIGNATURA_PESADA_CONSECUTIVA) == []
    assert validar(h.estado()) == []


def test_escenario_libera_una_franja_bloqueada() -> None:
    h = HorarioEnMemoria()
    curso = h.curso("6A")
    docente = h.docente("D1")
    bloque = h.bloque("B1")
    matematicas = h.asignatura("Matemáticas")
    h.habilitar(docente, matematicas)
    h.bloquear(docente, 1, bloque)
    sesion = h.colocar(h.asignacion(curso, matematicas, docente), 1, bloque)
    h.cambiar_escenario(docente, 1, bloque, disponible=True)
    estado = h.estado()

    base = _de(validar(estado), DOCENTE_NO_DISPONIBLE)
    con_escenario = _de(validar(estado, h.escenario_id), DOCENTE_NO_DISPONIBLE)

    assert base[0].sesion_ids == (sesion.id,)
    assert con_escenario == []
    # El escenario es overlay, no reemplazo: sin él el bloqueo sigue vigente (D-005).
    assert _de(validar(estado), DOCENTE_NO_DISPONIBLE) != []


def test_escenario_quita_una_franja_disponible() -> None:
    h = HorarioEnMemoria()
    curso = h.curso("6A")
    docente = h.docente("D1")
    bloque = h.bloque("B1")
    matematicas = h.asignatura("Matemáticas")
    h.habilitar(docente, matematicas)
    sesion = h.colocar(h.asignacion(curso, matematicas, docente), 1, bloque)
    h.cambiar_escenario(docente, 1, bloque, disponible=False)
    estado = h.estado()

    assert _de(validar(estado), DOCENTE_NO_DISPONIBLE) == []
    con_escenario = _de(validar(estado, h.escenario_id), DOCENTE_NO_DISPONIBLE)
    assert len(con_escenario) == 1
    assert con_escenario[0].sesion_ids == (sesion.id,)


def test_cambios_de_otro_escenario_no_se_aplican() -> None:
    h = HorarioEnMemoria()
    curso = h.curso("6A")
    docente = h.docente("D1")
    bloque = h.bloque("B1")
    matematicas = h.asignatura("Matemáticas")
    h.habilitar(docente, matematicas)
    h.colocar(h.asignacion(curso, matematicas, docente), 1, bloque)
    h.cambiar_escenario(docente, 1, bloque, disponible=False, escenario_id=uuid.uuid4())
    estado = h.estado()

    assert _de(validar(estado, h.escenario_id), DOCENTE_NO_DISPONIBLE) == []
    assert validar(estado) == []


def test_validar_no_importa_sqlalchemy_ni_la_ia() -> None:
    """Regla 1 de AGENTS.md, verificada en un intérprete limpio.

    `sys.modules` del proceso de pytest ya trae SQLAlchemy por otros tests, así que
    la comprobación corre en un subproceso que solo importa `app.validator`.
    """
    codigo = (
        "import sys\n"
        "import app.validator\n"
        "prohibidos = sorted(\n"
        "    modulo\n"
        "    for modulo in sys.modules\n"
        "    if modulo == 'sqlalchemy'\n"
        "    or modulo.startswith('sqlalchemy.')\n"
        "    or modulo == 'app.ai'\n"
        "    or modulo.startswith('app.ai.')\n"
        ")\n"
        "print(','.join(prohibidos))\n"
    )

    resultado = subprocess.run(
        [sys.executable, "-c", codigo],
        cwd=RUTA_API,
        capture_output=True,
        text=True,
        check=True,
    )

    assert resultado.stdout.strip() == ""


def test_rendimiento_120_sesiones() -> None:
    """El golden de la demo: 4 cursos × 5 días × 6 bloques, validado en <100 ms."""
    h = HorarioEnMemoria()
    bloques = [h.bloque(f"B{orden}") for orden in range(1, 7)]
    for codigo in ("6A", "6B", "7A", "7B"):
        curso = h.curso(codigo)
        recurso = h.recurso(f"Aula {codigo}", capacidad=30)
        cargas = []
        nombres = ("Matemáticas", "Lengua", "Ciencias", "Sociales", "Inglés")
        for indice, nombre in enumerate(nombres):
            asignatura = h.asignatura(f"{nombre} {codigo}")
            docente = h.docente(f"D-{codigo}-{indice}")
            h.habilitar(docente, asignatura)
            cargas.append(h.asignacion(curso, asignatura, docente, sesiones=6))
        # 5 días × 6 bloques = 30 franjas, 6 por asignatura.
        for dia in range(1, 6):
            for orden, bloque in enumerate(bloques):
                carga = cargas[(dia * 6 + orden) % len(cargas)]
                h.colocar(carga, dia, bloque, recurso=recurso)
    estado = h.estado()
    assert len(estado.sesiones) == 120

    validar(estado)  # calentamiento: importa cachés de dataclasses sin medirlos
    duraciones = []
    for _ in range(5):
        inicio = time.perf_counter()
        conflictos = validar(estado)
        duraciones.append(time.perf_counter() - inicio)

    mejor = min(duraciones)
    assert conflictos == []
    assert mejor < 0.1, f"validar() tardó {mejor * 1000:.1f} ms en 120 sesiones"
