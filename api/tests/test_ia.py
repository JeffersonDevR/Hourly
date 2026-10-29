"""Fase 8: parser determinista, reglas NL, filtro de propuestas de IA y cassette.

Golden 5: con `NullProvider` todo funciona y `/estado.ai_disponible` es false.
Golden 6: una propuesta de IA que introduce un choque se descarta.
"""

import dataclasses
import json
import uuid
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.ai import CassetteProvider, PropuestaIA, ReglaEstructurada, establecer_proveedor
from app.ai.base import AIError, CambioIA
from app.ai.reglas import interpretar_determinista
from app.db import get_session
from app.domain.catalogo import Aptitud, Bloque
from app.domain.conflictos import Conflicto as ConflictoDominio
from app.domain.enums import EstadoConflicto, Gravedad, TipoBloque, TipoCambioPropuesta
from app.domain.horario import Sesion
from app.main import app
from app.repositories.catalogo import (
    RepositorioAptitud,
    RepositorioBloque,
    RepositorioDocente,
)
from app.repositories.conflictos import RepositorioConflicto
from app.repositories.horario import RepositorioSesion
from app.services.horario import cargar_estado
from app.services.ia import proponer_con_ia
from tests.factories import BaseHorario, crear_base_horario


class ProveedorFijo:
    """Stub del proveedor: devuelve lo que el test guionó."""

    def __init__(
        self,
        propuestas: list[PropuestaIA] | None = None,
        regla: ReglaEstructurada | None = None,
        disponible: bool = True,
    ) -> None:
        self.propuestas = propuestas or []
        self.regla = regla
        self._disponible = disponible
        self.llamadas = 0

    def disponible(self) -> bool:
        return self._disponible

    def explicar_y_proponer(
        self, conflicto: dict[str, Any], contexto: dict[str, Any]
    ) -> list[PropuestaIA]:
        self.llamadas += 1
        return self.propuestas

    def interpretar_regla(
        self, texto: str, contexto: dict[str, Any]
    ) -> ReglaEstructurada | None:
        self.llamadas += 1
        return self.regla


@pytest.fixture(autouse=True)
def proveedor_limpio() -> Iterator[None]:
    """Cada test arranca con el proveedor del entorno (NullProvider sin claves)."""
    establecer_proveedor(None)
    yield
    establecer_proveedor(None)


@pytest.fixture
def cliente(sesion_db: Session) -> Iterator[TestClient]:
    app.dependency_overrides[get_session] = lambda: sesion_db
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()


# --- parser determinista (D-004) ----------------------------------------------------


@pytest.mark.parametrize(
    ("texto", "dias", "bloque", "bloquea"),
    [
        ("D1 no puede los martes", (2,), None, True),
        ("D3 libre el viernes B6", (5,), "B6", False),
        ("D2 no disponible lunes y miércoles", (1, 3), None, True),
        ("D4 sin clase el jueves", (4,), None, True),
        ("D6 no puede el lunes B1", (1,), "B1", True),
        ("d2 no puede los MIÉRCOLES", (3,), None, True),
    ],
)
def test_parser_determinista_cubre_las_formas(
    texto: str, dias: tuple[int, ...], bloque: str | None, bloquea: bool
) -> None:
    regla = interpretar_determinista(texto)

    assert regla is not None
    assert regla.dias == dias
    assert regla.bloque_codigo == bloque
    assert regla.bloquea is bloquea


@pytest.mark.parametrize(
    "texto",
    ["los docentes tienen que descansar", "D1 puede dar clases", "necesito 3 horas de inglés"],
)
def test_parser_determinista_no_inventa(texto: str) -> None:
    assert interpretar_determinista(texto) is None


def test_sin_proveedor_el_estado_dice_falso(cliente: TestClient) -> None:
    """Golden 5."""
    assert cliente.get("/api/estado").json()["ai_disponible"] is False


def test_con_proveedor_el_estado_dice_verdadero(cliente: TestClient) -> None:
    establecer_proveedor(ProveedorFijo())

    assert cliente.get("/api/estado").json()["ai_disponible"] is True


# --- reglas: interpretar y confirmar ------------------------------------------------


def test_interpretar_usa_el_parser_sin_proveedor(cliente: TestClient, sesion_db: Session) -> None:
    base = crear_base_horario(sesion_db)

    respuesta = cliente.post("/api/reglas/interpretar", json={"texto": "D1 no puede los martes"})

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["origen"] == "determinista"
    assert cuerpo["regla"]["docente_codigo"] == base.docente_a.codigo
    assert cuerpo["regla"]["dias"] == [2]
    assert cuerpo["mensaje"] is None


def test_interpretar_cae_en_manual_sin_proveedor(cliente: TestClient, sesion_db: Session) -> None:
    crear_base_horario(sesion_db)

    respuesta = cliente.post("/api/reglas/interpretar", json={"texto": "que no queden huecos"})

    cuerpo = respuesta.json()
    assert cuerpo["regla"] is None
    assert cuerpo["origen"] == "manual"
    assert "a mano" in cuerpo["mensaje"]


def test_interpretar_usa_la_ia_cuando_el_parser_no_matchea(
    cliente: TestClient, sesion_db: Session
) -> None:
    base = crear_base_horario(sesion_db)
    establecer_proveedor(
        ProveedorFijo(regla=ReglaEstructurada(docente_codigo="D1", dias=(2,), bloque_codigo=None))
    )

    cuerpo = cliente.post("/api/reglas/interpretar", json={"texto": "que no queden huecos"}).json()

    assert cuerpo["origen"] == "ia"
    assert cuerpo["regla"]["docente_codigo"] == base.docente_a.codigo


def test_confirmar_escribe_y_es_idempotente(cliente: TestClient, sesion_db: Session) -> None:
    base = crear_base_horario(sesion_db)
    cuerpo = {
        "docente_codigo": base.docente_a.codigo,
        "dias": [2, 3],
        "bloque_codigo": base.bloque.codigo,
        "bloquea": True,
        "motivo": "reunión",
    }

    primera = cliente.post("/api/reglas/confirmar", json=cuerpo)
    segunda = cliente.post("/api/reglas/confirmar", json=cuerpo)

    assert primera.status_code == 200, primera.text
    assert primera.json()["creados"] == 2
    assert segunda.json()["creados"] == 0  # UNIQUE(docente, dia, bloque): no duplica


def test_confirmar_liberar_borra_el_bloqueo(cliente: TestClient, sesion_db: Session) -> None:
    base = crear_base_horario(sesion_db)
    alta = {
        "docente_codigo": base.docente_a.codigo,
        "dias": [5],
        "bloque_codigo": base.bloque.codigo,
        "bloquea": True,
    }
    cliente.post("/api/reglas/confirmar", json=alta)

    baja = cliente.post("/api/reglas/confirmar", json={**alta, "bloquea": False})

    assert baja.json()["eliminados"] == 1


def test_confirmar_con_docente_inexistente_da_400(cliente: TestClient, sesion_db: Session) -> None:
    base = crear_base_horario(sesion_db)

    respuesta = cliente.post(
        "/api/reglas/confirmar",
        json={"docente_codigo": "D99", "dias": [1], "bloque_codigo": base.bloque.codigo},
    )

    assert respuesta.status_code == 400
    assert respuesta.json()["codigo"] == "REFERENCIA_INVALIDA"


# --- propuestas de IA: simular y descartar (regla 3, golden 6) -----------------------


@pytest.fixture
def base_dos_franjas(sesion_db: Session) -> tuple[BaseHorario, Bloque, Sesion, Sesion]:
    base = crear_base_horario(sesion_db)
    RepositorioAptitud(sesion_db).agregar(
        Aptitud(docente_id=base.docente_a.id, asignatura_id=base.asignatura.id)
    )
    segundo = RepositorioBloque(sesion_db).agregar(
        Bloque(
            codigo="B2",
            orden=2,
            inicio=base.bloque.inicio,
            fin=base.bloque.fin,
            duracion_min=60,
            tipo=TipoBloque.clase,
        )
    )
    repo = RepositorioSesion(sesion_db)
    lunes = repo.agregar(
        Sesion(
            horario_version_id=base.version.id,
            asignacion_carga_id=base.carga_a.id,
            curso_id=base.curso_a.id,
            docente_id=base.docente_a.id,
            dia=1,
            bloque_id=base.bloque.id,
        )
    )
    martes = repo.agregar(
        Sesion(
            horario_version_id=base.version.id,
            asignacion_carga_id=base.carga_a.id,
            curso_id=base.curso_a.id,
            docente_id=base.docente_a.id,
            dia=2,
            bloque_id=segundo.id,
        )
    )
    return base, segundo, lunes, martes


def test_ia_descarta_la_que_choca_y_conserva_la_buena(
    sesion_db: Session, base_dos_franjas: tuple[BaseHorario, Bloque, Sesion, Sesion]
) -> None:
    base, segundo, lunes, martes = base_dos_franjas
    conflicto = RepositorioConflicto(sesion_db).agregar(
        ConflictoDominio(
            horario_version_id=base.version.id,
            codigo="DOCENTE_DOBLE",
            gravedad=Gravedad.error,
            mensaje="D1 en dos lugares",
            estado=EstadoConflicto.abierto,
        )
    )
    establecer_proveedor(
        ProveedorFijo(
            propuestas=[
                # Choca con `martes`: mismo docente, mismo día y bloque.
                PropuestaIA(
                    titulo="Mover al martes",
                    explicacion="Rompe la regla",
                    impacto=None,
                    cambios=(
                        CambioIA(
                            tipo=TipoCambioPropuesta.mover_sesion,
                            sesion_id=lunes.id,
                            dia=2,
                            bloque_codigo=segundo.codigo,
                        ),
                    ),
                ),
                PropuestaIA(
                    titulo="Mover al miércoles",
                    explicacion="Franja libre",
                    impacto="Una sesión",
                    cambios=(
                        CambioIA(
                            tipo=TipoCambioPropuesta.mover_sesion,
                            sesion_id=lunes.id,
                            dia=3,
                            bloque_codigo=base.bloque.codigo,
                        ),
                    ),
                ),
            ]
        )
    )
    estado = cargar_estado(sesion_db, base.version)

    guardadas = proponer_con_ia(
        sesion_db,
        estado,
        {"codigo": "DOCENTE_DOBLE", "mensaje": "D1 en dos lugares", "sesion_ids": [str(lunes.id)]},
        None,
        conflicto.id,
    )

    assert [propuesta.titulo for propuesta in guardadas] == ["Mover al miércoles"]


def test_ia_sin_proveedor_no_propone_nada(
    sesion_db: Session, base_dos_franjas: tuple[BaseHorario, Bloque, Sesion, Sesion]
) -> None:
    base, _, lunes, _ = base_dos_franjas
    conflicto = RepositorioConflicto(sesion_db).agregar(
        ConflictoDominio(
            horario_version_id=base.version.id,
            codigo="DOCENTE_DOBLE",
            gravedad=Gravedad.error,
            mensaje="x",
            estado=EstadoConflicto.abierto,
        )
    )
    estado = cargar_estado(sesion_db, base.version)

    guardadas = proponer_con_ia(
        sesion_db,
        estado,
        {"codigo": "DOCENTE_DOBLE", "mensaje": "x", "sesion_ids": [str(lunes.id)]},
        None,
        conflicto.id,
    )

    assert guardadas == []


def test_generar_infactible_deja_el_motivo_en_conflictos(
    cliente: TestClient, sesion_db: Session
) -> None:
    base = crear_base_horario(sesion_db)
    RepositorioDocente(sesion_db).actualizar(
        dataclasses.replace(base.docente_a, max_sesiones_semana=0)
    )

    respuesta = cliente.post(
        f"/api/horarios/{base.version.id}/generar",
        json={"modo_docente": "principal"},
    )

    assert respuesta.json()["estado"] == "INFACTIBLE"
    codigos = {
        conflicto["codigo"]
        for conflicto in cliente.get(
            f"/api/horarios/{base.version.id}/conflictos"
        ).json()["conflictos"]
    }
    assert "DOCENTE_SOBRECARGA" in codigos


# --- cassette ------------------------------------------------------------------------


def test_cassette_replaya_cuando_el_proveedor_falla(tmp_path: Path) -> None:
    grabado = [
        {
            "titulo": "Pasar Inglés a D6",
            "explicacion": "D6 tiene cupo",
            "impacto": "Una sesión",
            "cambios": [
                {
                    "tipo": "cambiar_docente",
                    "sesion_id": str(uuid.uuid4()),
                    "docente_codigo": "D6",
                }
            ],
        }
    ]
    (tmp_path / "explicar_y_proponer.json").write_text(json.dumps(grabado), encoding="utf-8")

    class ProveedorCaido:
        def disponible(self) -> bool:
            return True

        def explicar_y_proponer(
            self, conflicto: dict[str, Any], contexto: dict[str, Any]
        ) -> list[PropuestaIA]:
            raise AIError("timeout")

        def interpretar_regla(
            self, texto: str, contexto: dict[str, Any]
        ) -> ReglaEstructurada | None:
            raise AIError("timeout")

    cassette = CassetteProvider(ProveedorCaido(), directorio=tmp_path)

    propuestas = cassette.explicar_y_proponer({}, {})

    assert cassette.disponible() is True
    assert [propuesta.titulo for propuesta in propuestas] == ["Pasar Inglés a D6"]


def test_cassette_sin_grabacion_y_sin_proveedor_falla(tmp_path: Path) -> None:
    class ProveedorCaido:
        def disponible(self) -> bool:
            return False

        def explicar_y_proponer(
            self, conflicto: dict[str, Any], contexto: dict[str, Any]
        ) -> list[PropuestaIA]:
            raise AIError("sin red")

        def interpretar_regla(
            self, texto: str, contexto: dict[str, Any]
        ) -> ReglaEstructurada | None:
            raise AIError("sin red")

    cassette = CassetteProvider(ProveedorCaido(), directorio=tmp_path)

    assert cassette.disponible() is False
    with pytest.raises(AIError):
        cassette.explicar_y_proponer({}, {})


def test_cassette_sembrado_cumple_el_contrato() -> None:
    """El cassette del repo no puede quedar roto: es el piso de la demo (D-002)."""
    from app.ai.cassette import DIRECTORIO_CASSETTES

    ruta = DIRECTORIO_CASSETTES / "interpretar_regla.json"
    assert ruta.exists(), "falta el cassette sembrado de interpretar_regla"

    class ProveedorCaido:
        def disponible(self) -> bool:
            return True

        def explicar_y_proponer(
            self, conflicto: dict[str, Any], contexto: dict[str, Any]
        ) -> list[PropuestaIA]:
            raise AIError("timeout")

        def interpretar_regla(
            self, texto: str, contexto: dict[str, Any]
        ) -> ReglaEstructurada | None:
            raise AIError("timeout")

    cassette = CassetteProvider(ProveedorCaido())

    regla = cassette.interpretar_regla("frase que el parser no entiende", {})

    assert cassette.disponible() is True
    assert regla is not None
    assert regla.docente_codigo.startswith("D")
    assert 1 <= regla.dias[0] <= 5
