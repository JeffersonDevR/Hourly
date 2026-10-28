"""Golden de la fase 4 sobre el archivo real (ARCHITECTURE.md:47-51).

Los hechos están verificados en `docs/DOMAIN.md` ("Hechos verificados con CP-SAT"):
120 sesiones, D4 28 > 24 con docente principal, D4/D6 repartible, D1 y D3 en 24/24.
El estado se arma con el importador de la fase 2, nunca a mano.

Ningún test de este archivo usa un dato inventado: los únicos estados sintéticos son
los de `test_solver_greedy.py` y `test_solver_recursos.py`, que prueban el motor con
casos mínimos.
"""

import subprocess
import sys
import time
from collections import Counter
from dataclasses import replace
from pathlib import Path

from app.domain.enums import Gravedad
from app.solver import EstadoResultado, resolver
from app.validator import ASIGNATURA_PESADA_CONSECUTIVA, DOCENTE_SOBRECARGA, validar
from tests.solverutil import ESCENARIO_ID, estado_demo, sesion_manual

RUTA_API = Path(__file__).resolve().parents[1]


def _errores(estado, escenario=None) -> list:
    return [
        conflicto
        for conflicto in validar(estado, escenario)
        if conflicto.gravedad == Gravedad.error
    ]


def _carga(resultado, estado) -> dict[str, int]:
    codigos = {docente.id: docente.codigo for docente in estado.docentes}
    return {
        codigos[docente_id]: sesiones
        for docente_id, sesiones in Counter(
            sesion.docente_id for sesion in resultado.sesiones
        ).items()
    }


def _clave_plan(sesion) -> tuple:
    """Identidad de una sesión en el plan, sin su UUID (que es uuid5, pero da igual)."""
    return (
        sesion.asignacion_carga_id,
        sesion.docente_id,
        sesion.dia,
        sesion.bloque_id,
        sesion.recurso_id,
    )


def test_golden_2_principal_es_infactible_por_d4() -> None:
    """`modo=principal`: D4 demanda 28 y su máximo es 24 → INFACTIBLE con causa."""
    estado = estado_demo()

    resultado = resolver(estado, modo_docente="principal")

    assert resultado.estado is EstadoResultado.INFACTIBLE
    assert resultado.sesiones == ()
    sobrecargas = [
        diagnostico
        for diagnostico in resultado.diagnostico
        if diagnostico.codigo == DOCENTE_SOBRECARGA
    ]
    assert len(sobrecargas) == 1
    over = sobrecargas[0]
    assert over.docente_codigo == "D4"
    assert (over.demanda, over.maximo) == (28, 24)
    assert "D4" in over.mensaje and "28" in over.mensaje and "24" in over.mensaje


def test_golden_3_habilitados_genera_120_sesiones_sin_errores() -> None:
    """Inglés repartible entre D4 y D6: 120 sesiones, `validar()` sin errores."""
    estado = estado_demo()

    resultado = resolver(estado, modo_docente="habilitados")

    assert resultado.estado in (EstadoResultado.OPTIMO, EstadoResultado.FACTIBLE)
    assert len(resultado.sesiones) == 120
    plan = replace(estado, sesiones=resultado.sesiones)
    assert _errores(plan) == []

    carga = _carga(resultado, estado)
    assert max(carga.values()) <= 24
    # Hechos verificados: D1 y D3 sin holgura, D4 y D6 reparten Inglés.
    assert carga["D1"] == 24
    assert carga["D3"] == 24
    assert carga["D2"] == 16
    assert carga["D5"] == 16
    assert carga["D4"] + carga["D6"] == 40
    assert carga["D4"] <= 24 and carga["D6"] <= 24


def test_golden_3_cada_curso_llena_su_semana_y_tiene_aula() -> None:
    """30 franjas por curso, una sesión por franja, y ninguna queda sin aula."""
    estado = estado_demo()
    resultado = resolver(estado, modo_docente="habilitados")

    por_curso: dict = Counter()
    por_franja: dict = Counter()
    for sesion in resultado.sesiones:
        por_curso[sesion.curso_id] += 1
        por_franja[(sesion.curso_id, sesion.dia, sesion.bloque_id)] += 1
    assert set(por_curso.values()) == {30}
    assert set(por_franja.values()) == {1}
    assert all(sesion.recurso_id is not None for sesion in resultado.sesiones)


def test_golden_4_escenario_d2_sin_martes() -> None:
    """Con el escenario, D2 no tiene ninguna sesión el martes y el plan sigue limpio."""
    estado = estado_demo()

    resultado = resolver(estado, modo_docente="habilitados", escenario=ESCENARIO_ID)

    assert resultado.estado in (EstadoResultado.OPTIMO, EstadoResultado.FACTIBLE)
    assert len(resultado.sesiones) == 120
    d2 = next(docente for docente in estado.docentes if docente.codigo == "D2")
    martes = [
        sesion
        for sesion in resultado.sesiones
        if sesion.docente_id == d2.id and sesion.dia == 2
    ]
    assert martes == []
    plan = replace(estado, sesiones=resultado.sesiones)
    assert _errores(plan, ESCENARIO_ID) == []


def test_golden_4_fijas_una_sesion_puesta_a_mano_no_se_mueve() -> None:
    """D-008: las sesiones existentes son `fijas`; el resto se genera alrededor."""
    estado = estado_demo()
    a_mano = sesion_manual(estado, "6A", "Matemáticas", dia=1, bloque="B1", docente="D1")
    estado = replace(estado, sesiones=(a_mano,))

    resultado = resolver(estado, modo_docente="habilitados")

    assert len(resultado.sesiones) == 120
    misma = [
        sesion
        for sesion in resultado.sesiones
        if sesion.id == a_mano.id
    ]
    assert len(misma) == 1
    assert (misma[0].dia, misma[0].bloque_id, misma[0].docente_id) == (
        a_mano.dia,
        a_mano.bloque_id,
        a_mano.docente_id,
    )
    assert _errores(replace(estado, sesiones=resultado.sesiones)) == []


def test_limpiar_descarta_las_sesiones_existentes() -> None:
    """`limpiar=True` es lo único que las borra (D-008)."""
    estado = estado_demo()
    a_mano = sesion_manual(estado, "6A", "Matemáticas", dia=1, bloque="B1", docente="D1")
    estado = replace(estado, sesiones=(a_mano,))

    resultado = resolver(estado, modo_docente="habilitados", limpiar=True)

    assert len(resultado.sesiones) == 120
    assert all(sesion.id != a_mano.id for sesion in resultado.sesiones)


def test_determinismo_mismo_input_mismo_plan() -> None:
    """Un worker y semilla fija: dos corridas devuelven el mismo plan y objetivo."""
    estado = estado_demo()

    primera = resolver(estado, modo_docente="habilitados")
    segunda = resolver(estado, modo_docente="habilitados")

    assert primera.objetivo == segunda.objetivo
    assert [_clave_plan(sesion) for sesion in primera.sesiones] == [
        _clave_plan(sesion) for sesion in segunda.sesiones
    ]


def test_docente_nunca_usa_una_franja_bloqueada() -> None:
    """D1 tiene bloqueado el viernes B6 en el archivo real."""
    estado = estado_demo()
    resultado = resolver(estado, modo_docente="habilitados")
    viernes, b6 = 5, next(bloque for bloque in estado.bloques if bloque.codigo == "B6")
    bloqueado = estado.bloqueos[0].docente_id

    assert [
        sesion
        for sesion in resultado.sesiones
        if sesion.dia == viernes
        and sesion.bloque_id == b6.id
        and sesion.docente_id == bloqueado
    ] == []


def test_penalizacion_de_pesadas_es_blanda_y_medible() -> None:
    """D-006: marcar dos asignaturas como pesadas y comparar con y sin penalidad.

    El Excel no trae `es_pesada`, así que la regla solo se puede medir marcando
    asignaturas en el estado. La penalidad nunca puede volver INFACTIBLE el modelo:
    con la grilla llena, la versión dura rompería el golden 3.
    """
    estado = estado_demo(pesadas={"Matemáticas", "Ciencias sociales"})

    sin_penalidad = resolver(estado, modo_docente="habilitados", peso_pesadas=0)
    con_penalidad = resolver(estado, modo_docente="habilitados")

    assert con_penalidad.estado in (EstadoResultado.OPTIMO, EstadoResultado.FACTIBLE)
    assert len(con_penalidad.sesiones) == 120

    sin = len(
        [
            conflicto
            for conflicto in validar(replace(estado, sesiones=sin_penalidad.sesiones))
            if conflicto.codigo == ASIGNATURA_PESADA_CONSECUTIVA
        ]
    )
    con = len(
        [
            conflicto
            for conflicto in validar(replace(estado, sesiones=con_penalidad.sesiones))
            if conflicto.codigo == ASIGNATURA_PESADA_CONSECUTIVA
        ]
    )
    assert con <= sin, f"la penalidad empeoró la adyacencia pesada: {sin} → {con}"


def test_rendimiento_generacion_de_la_demo() -> None:
    """El criterio de la fase: la generación completa muy por debajo de 10 s."""
    estado = estado_demo()

    inicio = time.perf_counter()
    resultado = resolver(estado, modo_docente="habilitados")
    transcurrido = time.perf_counter() - inicio

    assert len(resultado.sesiones) == 120
    assert transcurrido < 10.0, f"la generación tardó {transcurrido:.2f} s"


def test_solver_no_importa_sqlalchemy_ni_la_ia() -> None:
    """Regla 2 de AGENTS.md, verificada en un intérprete limpio."""
    codigo = (
        "import sys\n"
        "import app.solver\n"
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
