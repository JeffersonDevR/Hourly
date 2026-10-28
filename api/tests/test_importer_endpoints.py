"""Endpoints de importación: multipart, PATCH de filas, confirmar y plantilla.

Usan el `TestClient` sobre la app real con `get_session` apuntando a la DB temporal
del test: el mismo camino que ejecuta la demo, sin servidor.
"""

from collections.abc import Iterator
from io import BytesIO
from pathlib import Path

import openpyxl
import pytest
import sqlalchemy as sa
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db import get_session
from app.importer.lectura import ENCABEZADOS
from app.main import app
from app.models.carga import AsignacionCargaDB, DisponibilidadBloqueoDB
from app.models.catalogo import AptitudDB, CursoDB
from app.models.procesos import ImportacionDB, ImportacionErrorDB
from tests.xlsxutil import libro_minimo

DATOS = Path(__file__).resolve().parents[2] / "data" / "Datos_prueba_Gnosoft.xlsx"
MEDIA_XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


@pytest.fixture
def cliente(sesion_db: Session) -> Iterator[TestClient]:
    """App real + la sesión del test como dependencia (sin tocar `hourly.db`)."""
    app.dependency_overrides[get_session] = lambda: sesion_db
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()


def _subir(cliente: TestClient, contenido: bytes, nombre: str = "libro.xlsx") -> dict:
    respuesta = cliente.post(
        "/api/importaciones", files={"archivo": (nombre, contenido, MEDIA_XLSX)}
    )
    assert respuesta.status_code == 200, respuesta.text
    return respuesta.json()


def _contar(sesion: Session, modelo: type) -> int:
    return sesion.scalar(sa.select(sa.func.count()).select_from(modelo)) or 0


def test_post_importaciones_devuelve_preview_y_persiste(
    cliente: TestClient, sesion_db: Session
) -> None:
    cuerpo = _subir(cliente, DATOS.read_bytes(), DATOS.name)

    assert cuerpo["estado"] == "preview"
    assert cuerpo["archivo_nombre"] == DATOS.name
    assert cuerpo["conteos"]["aptitudes"] == 11
    assert cuerpo["conteos"]["asignaciones"] == 40
    assert cuerpo["conteos"]["bloqueos"] == 1
    assert "DOCENTE_SOBRECARGA" in cuerpo["codigos"]
    assert "DURACION_BLOQUE_INCONSISTENTE" in cuerpo["codigos"]
    assert cuerpo["confirmable"] is True

    assert _contar(sesion_db, ImportacionDB) == 1
    assert _contar(sesion_db, ImportacionErrorDB) == len(cuerpo["hallazgos"])
    # Nada de negocio se escribió en el preview.
    assert _contar(sesion_db, CursoDB) == 0


def test_confirmar_escribe_y_es_idempotente(cliente: TestClient, sesion_db: Session) -> None:
    primera = _subir(cliente, DATOS.read_bytes(), DATOS.name)
    confirmada = cliente.post(f"/api/importaciones/{primera['id']}/confirmar")

    assert confirmada.status_code == 200
    cuerpo = confirmada.json()
    assert cuerpo["estado"] == "confirmada"
    assert cuerpo["escritura"]["creados"]["asignacion_carga"] == 40
    conteos = {
        "cursos": _contar(sesion_db, CursoDB),
        "aptitudes": _contar(sesion_db, AptitudDB),
        "asignaciones": _contar(sesion_db, AsignacionCargaDB),
        "bloqueos": _contar(sesion_db, DisponibilidadBloqueoDB),
    }
    assert conteos == {"cursos": 4, "aptitudes": 11, "asignaciones": 40, "bloqueos": 1}

    # Segundo archivo idéntico: ni una fila nueva, ni una excepción (D-009).
    segunda = _subir(cliente, DATOS.read_bytes(), DATOS.name)
    otra_vez = cliente.post(f"/api/importaciones/{segunda['id']}/confirmar")

    assert otra_vez.status_code == 200
    assert otra_vez.json()["escritura"]["creados"] == {}
    assert {
        "cursos": _contar(sesion_db, CursoDB),
        "aptitudes": _contar(sesion_db, AptitudDB),
        "asignaciones": _contar(sesion_db, AsignacionCargaDB),
        "bloqueos": _contar(sesion_db, DisponibilidadBloqueoDB),
    } == conteos


def test_patch_corrige_una_celda_y_revalida(cliente: TestClient, sesion_db: Session) -> None:
    cuerpo = _subir(cliente, libro_minimo(curso_malo=True))
    assert "CURSO_NO_RECONOCIDO" in cuerpo["codigos"]
    assert cuerpo["conteos"]["asignaciones"] == 9

    hallazgo = next(h for h in cuerpo["hallazgos"] if h["codigo"] == "CURSO_NO_RECONOCIDO")
    correccion = cliente.patch(
        f"/api/importaciones/{cuerpo['id']}/filas",
        json={
            "correcciones": [
                {
                    "hoja": hallazgo["hoja"],
                    "fila": hallazgo["fila"],
                    "columna": hallazgo["columna"],
                    "valor": "7A",
                }
            ]
        },
    )

    assert correccion.status_code == 200, correccion.text
    revalidado = correccion.json()
    assert "CURSO_NO_RECONOCIDO" not in revalidado["codigos"]
    assert revalidado["conteos"]["asignaciones"] == 10
    # El análisis es autoritativo: los hallazgos viejos no quedan colgados.
    assert _contar(sesion_db, ImportacionErrorDB) == len(revalidado["hallazgos"])

    assert cliente.post(f"/api/importaciones/{cuerpo['id']}/confirmar").status_code == 200
    assert _contar(sesion_db, AsignacionCargaDB) == 10


def test_patch_con_columna_inexistente_da_422(cliente: TestClient) -> None:
    cuerpo = _subir(cliente, libro_minimo())

    respuesta = cliente.patch(
        f"/api/importaciones/{cuerpo['id']}/filas",
        json={
            "correcciones": [
                {"hoja": "Cursos", "fila": 2, "columna": "inexistente", "valor": 1}
            ]
        },
    )

    assert respuesta.status_code == 422


def test_confirmar_importacion_inexistente_da_404(cliente: TestClient) -> None:
    respuesta = cliente.post(
        "/api/importaciones/00000000-0000-4000-8000-000000000000/confirmar"
    )

    assert respuesta.status_code == 404


def test_archivo_que_no_es_xlsx_da_400(cliente: TestClient) -> None:
    respuesta = cliente.post(
        "/api/importaciones", files={"archivo": ("libro.xlsx", b"no soy un excel", MEDIA_XLSX)}
    )

    assert respuesta.status_code == 400


def test_plantilla_devuelve_xlsx_con_las_hojas_esperadas(cliente: TestClient) -> None:
    respuesta = cliente.get("/api/importaciones/plantilla")

    assert respuesta.status_code == 200
    assert respuesta.headers["content-type"].startswith(MEDIA_XLSX)
    assert "attachment" in respuesta.headers["content-disposition"]

    libro = openpyxl.load_workbook(BytesIO(respuesta.content))
    assert libro.sheetnames == list(ENCABEZADOS)
    assert tuple(celda.value for celda in libro["Carga"][1]) == ENCABEZADOS["Carga"]
    assert tuple(celda.value for celda in libro["Disponibilidad"][1]) == (
        ENCABEZADOS["Disponibilidad"]
    )
