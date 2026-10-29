"""Fase 9: escenario "¿y si…?" (preview sin escribir, aplicar) y exportación PDF."""

from collections.abc import Iterator
from dataclasses import replace
from io import BytesIO

import openpyxl
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db import get_session
from app.domain.catalogo import Aptitud
from app.domain.enums import EstadoVersion
from app.domain.horario import Escenario, EscenarioCambio, Sesion
from app.main import app
from app.repositories.catalogo import RepositorioAptitud
from app.repositories.horario import (
    RepositorioEscenario,
    RepositorioEscenarioCambio,
    RepositorioHorarioVersion,
    RepositorioSesion,
)
from app.services.horario import cargar_estado
from tests.factories import BaseHorario, crear_base_horario


@pytest.fixture
def cliente(sesion_db: Session) -> Iterator[TestClient]:
    app.dependency_overrides[get_session] = lambda: sesion_db
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()


@pytest.fixture
def con_escenario(sesion_db: Session) -> tuple[BaseHorario, Escenario]:
    """Base mínima + D1 sin clase el lunes, con una sesión justo en esa franja."""
    base = crear_base_horario(sesion_db)
    for docente in (base.docente_a, base.docente_b):
        RepositorioAptitud(sesion_db).agregar(
            Aptitud(docente_id=docente.id, asignatura_id=base.asignatura.id)
        )
    escenario = RepositorioEscenario(sesion_db).agregar(
        Escenario(nombre="D1 sin lunes", descripcion="Prueba")
    )
    RepositorioEscenarioCambio(sesion_db).agregar(
        EscenarioCambio(
            escenario_id=escenario.id,
            docente_id=base.docente_a.id,
            dia=1,
            bloque_id=base.bloque.id,
            disponible_nuevo=False,
        )
    )
    RepositorioSesion(sesion_db).agregar(
        Sesion(
            horario_version_id=base.version.id,
            asignacion_carga_id=base.carga_a.id,
            curso_id=base.curso_a.id,
            docente_id=base.docente_a.id,
            dia=1,
            bloque_id=base.bloque.id,
        )
    )
    return base, escenario


def _url(base: BaseHorario) -> str:
    return f"/api/horarios/{base.version.id}/escenario"


def test_preview_no_escribe_nada(
    cliente: TestClient,
    sesion_db: Session,
    con_escenario: tuple[BaseHorario, Escenario],
) -> None:
    base, escenario = con_escenario

    respuesta = cliente.post(_url(base), json={"escenario_id": str(escenario.id)})

    assert respuesta.status_code == 200, respuesta.text
    cuerpo = respuesta.json()
    assert cuerpo["aplicado"] is False
    assert cuerpo["sesiones_afectadas"] == 1
    assert cuerpo["resultado"]["estado"] in {"OPTIMO", "FACTIBLE"}
    # Nada se persistió: ni el escenario de la versión ni las sesiones.
    assert RepositorioHorarioVersion(sesion_db).obtener(base.version.id).escenario_id is None
    assert len(RepositorioSesion(sesion_db).listar_por_version(base.version.id)) == 1


def test_aplicar_fija_el_escenario_y_limpia_el_conflicto(
    cliente: TestClient,
    sesion_db: Session,
    con_escenario: tuple[BaseHorario, Escenario],
) -> None:
    base, escenario = con_escenario

    respuesta = cliente.post(
        _url(base), json={"escenario_id": str(escenario.id), "aplicar": True}
    )

    assert respuesta.status_code == 200, respuesta.text
    cuerpo = respuesta.json()
    assert cuerpo["aplicado"] is True
    guardada = RepositorioHorarioVersion(sesion_db).obtener(base.version.id)
    assert guardada.escenario_id == escenario.id
    assert "DOCENTE_NO_DISPONIBLE" not in {item["codigo"] for item in cuerpo["conflictos"]}
    # La sesión que caía en la franja bloqueada se reubicó.
    sesiones = RepositorioSesion(sesion_db).listar_por_version(base.version.id)
    assert sesiones
    assert all(
        not (sesion.dia == 1 and sesion.docente_id == base.docente_a.id) for sesion in sesiones
    )


def test_el_estado_carga_el_overlay_aunque_la_version_no_lo_tenga(
    sesion_db: Session, con_escenario: tuple[BaseHorario, Escenario]
) -> None:
    """Regresión: el preview resolvía sin `escenario_cambios` y colocaba sesiones en
    franjas bloqueadas. El overlay se pide explícito, no se deduce de la versión."""
    base, escenario = con_escenario

    estado = cargar_estado(sesion_db, base.version, escenario.id)

    assert len(estado.escenario_cambios) == 1
    assert estado.escenario_cambios[0].docente_id == base.docente_a.id


def test_escenario_inexistente_da_404(
    cliente: TestClient, con_escenario: tuple[BaseHorario, Escenario]
) -> None:
    base, _ = con_escenario

    respuesta = cliente.post(
        _url(base), json={"escenario_id": "00000000-0000-0000-0000-000000000000"}
    )

    assert respuesta.status_code == 404
    assert respuesta.json()["codigo"] == "NO_ENCONTRADO"


def test_version_publicada_no_prueba_escenarios(
    cliente: TestClient,
    sesion_db: Session,
    con_escenario: tuple[BaseHorario, Escenario],
) -> None:
    base, escenario = con_escenario
    RepositorioHorarioVersion(sesion_db).actualizar(
        replace(base.version, estado=EstadoVersion.publicado)
    )

    respuesta = cliente.post(_url(base), json={"escenario_id": str(escenario.id)})

    assert respuesta.status_code == 409
    assert respuesta.json()["codigo"] == "VERSION_PUBLICADA"


def test_exportar_pdf_produce_un_pdf(cliente: TestClient, sesion_db: Session) -> None:
    base = crear_base_horario(sesion_db)

    respuesta = cliente.get(
        f"/api/horarios/{base.version.id}/exportar",
        params={"formato": "pdf", "por": "general"},
    )

    assert respuesta.status_code == 200
    assert respuesta.headers["content-type"] == "application/pdf"
    assert respuesta.content.startswith(b"%PDF")
    assert len(respuesta.content) > 1000


def test_exportar_xlsx_sigue_funcionando(cliente: TestClient, sesion_db: Session) -> None:
    base = crear_base_horario(sesion_db)

    respuesta = cliente.get(
        f"/api/horarios/{base.version.id}/exportar", params={"por": "general"}
    )

    libro = openpyxl.load_workbook(BytesIO(respuesta.content))
    assert libro.sheetnames == ["6A", "6B"]
