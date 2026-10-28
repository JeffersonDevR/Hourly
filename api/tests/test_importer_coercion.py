"""Coerción de celdas: el bug más caro de la fase 2 (`DOMAIN.md`, trampas 1, 2 y 5).

Esta suite es la que impide que alguien "simplifique" `a_booleano` a `valor == "1"`:
con el archivo real (`1.0`), esa comparación devuelve `False` y la importación pierde
todas las aptitudes y bloqueos sin lanzar una sola excepción.
"""

from datetime import time

import pytest

from app.importer.coercion import (
    a_booleano,
    a_dia,
    a_entero,
    a_hora,
    a_texto,
    minutos,
    sin_acentos,
)


@pytest.mark.parametrize("valor", [1, 1.0, "1", "1.0", True, "sí", "SI", "x", 2.5])
def test_a_booleano_verdadero(valor: object) -> None:
    assert a_booleano(valor) is True


@pytest.mark.parametrize("valor", [0, 0.0, "0", "0.0", False, "no", "No"])
def test_a_booleano_falso(valor: object) -> None:
    assert a_booleano(valor) is False


@pytest.mark.parametrize("valor", [None, "", "   ", "quizá", "n/a"])
def test_a_booleano_desconocido_devuelve_none(valor: object) -> None:
    assert a_booleano(valor) is None


def test_float_uno_no_es_la_cadena_uno() -> None:
    """La trampa, explícita: `1.0 == "1"` es False, por eso se compara numérico."""
    assert 1.0 == 1
    assert 1.0 != "1"
    assert a_booleano(1.0) is True
    assert a_booleano("1") is True


@pytest.mark.parametrize(
    ("valor", "esperado"),
    [
        (30.0, 30),
        ("30", 30),
        ("30.0", 30),
        (30, 30),
        ("30,0", 30),
        (None, None),
        ("", None),
        ("treinta", None),
        (30.5, None),
    ],
)
def test_a_entero(valor: object, esperado: int | None) -> None:
    assert a_entero(valor) == esperado


@pytest.mark.parametrize(
    ("valor", "esperado"),
    [
        (time(7, 0), time(7, 0)),
        (0.2916667, time(7, 0)),  # serial de Excel: 0.2916667 * 24 * 60 = 420
        (0.5, time(12, 0)),
        ("07:00", time(7, 0)),
        ("07:00:00", time(7, 0)),
        ("7:00", time(7, 0)),
        (None, None),
        ("", None),
        ("no es una hora", None),
    ],
)
def test_a_hora(valor: object, esperado: time | None) -> None:
    assert a_hora(valor) == esperado


@pytest.mark.parametrize(
    ("minuto", "esperado"),
    [(420, time(7, 0)), (480, time(8, 0)), (540, time(9, 0)), (720, time(12, 0))],
)
def test_serial_de_excel_a_hora(minuto: int, esperado: time) -> None:
    """Los seis bloques del archivo real: 07:00–13:00 en pasos de 60 min."""
    assert a_hora(minuto / (24 * 60)) == esperado
    assert minutos(a_hora(minuto / (24 * 60))) == minuto


@pytest.mark.parametrize(
    ("valor", "esperado"),
    [
        ("Lunes", 1),
        ("martes", 2),
        ("Miércoles", 3),
        ("MIERCOLES", 3),
        ("Jueves", 4),
        ("Viernes", 5),
        (2, 2),
        (2.0, 2),
        ("Sábado", None),
        ("Funday", None),
        (None, None),
        ("", None),
    ],
)
def test_a_dia(valor: object, esperado: int | None) -> None:
    assert a_dia(valor) == esperado


@pytest.mark.parametrize(
    ("valor", "esperado"),
    [("6", "6"), (6.0, "6"), (6, "6"), ("  7A  ", "7A"), ("", None), (None, None)],
)
def test_a_texto(valor: object, esperado: str | None) -> None:
    assert a_texto(valor) == esperado


def test_sin_acentos_normaliza_para_comparar() -> None:
    assert sin_acentos("  Miércoles ") == "miercoles"
    assert sin_acentos("Asignaturas   docentes") == "asignaturas docentes"
