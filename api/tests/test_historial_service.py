"""`app.services.historial`: el único escritor de `historial_cambio` (fase 1).

Los routers llegan en la fase 5; acá se prueba el contrato del servicio y su lectura
posterior, incluido el caso de una entidad cuya PK no es UUID (`tipo_recurso`).
"""

import pytest
from sqlalchemy.orm import Session

from app.domain.procesos import HistorialCambio
from app.repositories.horario import RepositorioSesion
from app.repositories.procesos import RepositorioHistorial
from app.services.historial import registrar_cambio
from tests.factories import BaseHorario, crear_base_horario, sesion_en_primera_franja


def test_servicio_escribe_y_se_lee(sesion_db: Session) -> None:
    base = crear_base_horario(sesion_db)
    sesion = RepositorioSesion(sesion_db).agregar(sesion_en_primera_franja(base))

    entrada = registrar_cambio(
        sesion_db,
        entidad="sesion",
        entidad_id=sesion.id,
        accion="crear",
        despues={"dia": 1, "bloque": "B1", "docente": "D1"},
        horario_version_id=base.version.id,
    )

    assert isinstance(entrada, HistorialCambio)
    assert entrada.entidad_id == str(sesion.id)

    sesion_db.expunge_all()
    leidas = RepositorioHistorial(sesion_db).listar_por_version(base.version.id)

    assert len(leidas) == 1
    assert leidas[0].entidad == "sesion"
    assert leidas[0].accion == "crear"
    assert leidas[0].antes is None
    assert leidas[0].despues == {"dia": 1, "bloque": "B1", "docente": "D1"}
    assert leidas[0].ocurrido_at is not None


def test_mover_guarda_antes_y_despues(sesion_db: Session) -> None:
    base = crear_base_horario(sesion_db)

    registrar_cambio(
        sesion_db,
        entidad="sesion",
        entidad_id="00000000-0000-0000-0000-000000000001",
        accion="mover",
        antes={"dia": 1, "bloque": "B1"},
        despues={"dia": 2, "bloque": "B3"},
        horario_version_id=base.version.id,
    )

    leidas = RepositorioHistorial(sesion_db).listar_por_version(base.version.id)
    assert [leida.accion for leida in leidas] == ["mover"]
    assert leidas[0].antes == {"dia": 1, "bloque": "B1"}
    assert leidas[0].despues == {"dia": 2, "bloque": "B3"}


def test_acepta_pk_que_no_es_uuid_y_version_nula(sesion_db: Session) -> None:
    """`tipo_recurso.codigo` es la PK y es texto; el cambio de catálogo no tiene versión."""
    entrada = registrar_cambio(
        sesion_db,
        entidad="tipo_recurso",
        entidad_id="LAB_CIENCIAS",
        accion="crear",
        despues={"codigo": "LAB_CIENCIAS"},
    )

    assert entrada.entidad_id == "LAB_CIENCIAS"

    leidas = RepositorioHistorial(sesion_db).listar()
    assert len(leidas) == 1
    assert leidas[0].horario_version_id is None


def test_historial_no_se_escribe_desde_el_repositorio(sesion_db: Session) -> None:
    """Regla 3 de AGENTS.md hecha estructural: el repositorio es solo lectura."""
    repositorio = RepositorioHistorial(sesion_db)
    entrada = HistorialCambio(entidad="sesion", entidad_id="x", accion="crear")

    with pytest.raises(NotImplementedError):
        repositorio.agregar(entrada)


def test_historial_ordena_por_ocurrencia(sesion_db: Session) -> None:
    base: BaseHorario = crear_base_horario(sesion_db)
    for accion in ("crear", "mover", "eliminar"):
        registrar_cambio(
            sesion_db,
            entidad="sesion",
            entidad_id="00000000-0000-0000-0000-000000000002",
            accion=accion,
            horario_version_id=base.version.id,
        )

    leidas = RepositorioHistorial(sesion_db).listar_por_version(base.version.id)
    assert [leida.accion for leida in leidas] == ["crear", "mover", "eliminar"]
