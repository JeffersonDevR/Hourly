"""CRUD de catálogos: contrato HTTP y traducción de las reglas de la DB a 4xx."""

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db import get_session
from app.domain.carga import AsignacionCarga
from app.domain.catalogo import Asignatura, Curso, Docente, Grado
from app.domain.recursos import Recurso, TipoRecurso
from app.main import app
from app.repositories.carga import RepositorioAsignacionCarga
from app.repositories.catalogo import (
    RepositorioAsignatura,
    RepositorioCurso,
    RepositorioDocente,
    RepositorioGrado,
)
from app.repositories.recursos import RepositorioRecurso, RepositorioTipoRecurso


@pytest.fixture
def cliente(sesion_db: Session) -> Iterator[TestClient]:
    app.dependency_overrides[get_session] = lambda: sesion_db
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()


@pytest.fixture
def grado(sesion_db: Session) -> Grado:
    return RepositorioGrado(sesion_db).agregar(Grado(nombre="6", orden=6))


@pytest.fixture
def curso(sesion_db: Session, grado: Grado) -> Curso:
    return RepositorioCurso(sesion_db).agregar(
        Curso(codigo="6A", nombre="Sexto A", grado_id=grado.id, estudiantes=30)
    )


def _error(respuesta: object) -> dict:
    """El cuerpo de error es `{codigo, mensaje}` en el nivel superior."""
    cuerpo = respuesta.json()  # type: ignore[attr-defined]
    assert set(cuerpo) == {"codigo", "mensaje"}, cuerpo
    return cuerpo


def test_crud_curso_completo(cliente: TestClient, grado: Grado) -> None:
    creado = cliente.post(
        "/api/cursos",
        json={"codigo": "7B", "nombre": "Séptimo B", "grado_id": str(grado.id), "estudiantes": 28},
    )
    assert creado.status_code == 201, creado.text
    curso_id = creado.json()["id"]

    assert [c["codigo"] for c in cliente.get("/api/cursos").json()] == ["7B"]
    assert cliente.get(f"/api/cursos/{curso_id}").json()["estudiantes"] == 28

    parcheado = cliente.patch(f"/api/cursos/{curso_id}", json={"estudiantes": 31})
    assert parcheado.status_code == 200
    assert parcheado.json()["estudiantes"] == 31

    assert cliente.delete(f"/api/cursos/{curso_id}").status_code == 204
    assert cliente.get(f"/api/cursos/{curso_id}").status_code == 404


def test_curso_inexistente_devuelve_404_con_codigo(cliente: TestClient) -> None:
    respuesta = cliente.get("/api/cursos/00000000-0000-0000-0000-000000000000")

    assert respuesta.status_code == 404
    assert _error(respuesta)["codigo"] == "NO_ENCONTRADO"


def test_curso_codigo_duplicado_devuelve_409(cliente: TestClient, grado: Grado) -> None:
    cliente.post(
        "/api/cursos",
        json={"codigo": "6A", "nombre": "A", "grado_id": str(grado.id), "estudiantes": 30},
    )
    respuesta = cliente.post(
        "/api/cursos",
        json={"codigo": "6A", "nombre": "B", "grado_id": str(grado.id), "estudiantes": 30},
    )

    assert respuesta.status_code == 409
    assert _error(respuesta)["codigo"] == "CODIGO_DUPLICADO"


def test_curso_con_grado_inexistente_devuelve_400(cliente: TestClient) -> None:
    respuesta = cliente.post(
        "/api/cursos",
        json={
            "codigo": "8A",
            "nombre": "Octavo",
            "grado_id": "00000000-0000-0000-0000-000000000000",
            "estudiantes": 30,
        },
    )

    assert respuesta.status_code == 400
    assert _error(respuesta)["codigo"] == "REFERENCIA_INVALIDA"


def test_borrar_curso_referenciado_devuelve_409(
    cliente: TestClient, curso: Curso, sesion_db: Session
) -> None:
    asignatura = RepositorioAsignatura(sesion_db).agregar(
        Asignatura(nombre="Matemática", color="#111111")
    )
    docente = RepositorioDocente(sesion_db).agregar(
        Docente(codigo="D1", nombre="Ana", max_sesiones_semana=24)
    )
    RepositorioTipoRecurso(sesion_db).agregar(TipoRecurso(codigo="GENERAL"))
    RepositorioAsignacionCarga(sesion_db).agregar(
        AsignacionCarga(
            curso_id=curso.id,
            asignatura_id=asignatura.id,
            docente_principal_id=docente.id,
            sesiones_semana=5,
            tipo_recurso_requerido="GENERAL",
        )
    )

    respuesta = cliente.delete(f"/api/cursos/{curso.id}")

    assert respuesta.status_code == 409
    assert _error(respuesta)["codigo"] == "EN_USO"
    assert cliente.get(f"/api/cursos/{curso.id}").status_code == 200


def test_patch_docente_y_listado(cliente: TestClient) -> None:
    creado = cliente.post(
        "/api/docentes", json={"codigo": "D4", "nombre": "Luis", "max_sesiones_semana": 24}
    )
    docente_id = creado.json()["id"]

    assert (
        cliente.patch(f"/api/docentes/{docente_id}", json={"activo": False}).json()["activo"]
        is False
    )
    assert cliente.get("/api/docentes").json()[0]["codigo"] == "D4"


def test_recurso_con_tipo_inexistente_devuelve_400(cliente: TestClient) -> None:
    respuesta = cliente.post(
        "/api/recursos",
        json={
            "codigo": "AULA-6A",
            "nombre": "Aula 6A",
            "tipo_recurso": "NO_EXISTE",
            "capacidad": 30,
        },
    )

    assert respuesta.status_code == 400
    assert _error(respuesta)["codigo"] == "REFERENCIA_INVALIDA"


def test_asignacion_duplicada_devuelve_409(
    cliente: TestClient, curso: Curso, sesion_db: Session
) -> None:
    asignatura = RepositorioAsignatura(sesion_db).agregar(
        Asignatura(nombre="Inglés", color="#222222")
    )
    docente = RepositorioDocente(sesion_db).agregar(
        Docente(codigo="D6", nombre="Eva", max_sesiones_semana=24)
    )
    RepositorioTipoRecurso(sesion_db).agregar(TipoRecurso(codigo="GENERAL"))
    cuerpo = {
        "curso_id": str(curso.id),
        "asignatura_id": str(asignatura.id),
        "docente_principal_id": str(docente.id),
        "sesiones_semana": 4,
        "tipo_recurso_requerido": "GENERAL",
    }

    assert cliente.post("/api/asignaciones", json=cuerpo).status_code == 201
    respuesta = cliente.post("/api/asignaciones", json=cuerpo)

    assert respuesta.status_code == 409
    assert _error(respuesta)["codigo"] == "ASIGNACION_DUPLICADA"


def test_recursos_y_asignaciones_se_filtran_por_curso(
    cliente: TestClient, curso: Curso, sesion_db: Session
) -> None:
    RepositorioTipoRecurso(sesion_db).agregar(TipoRecurso(codigo="GENERAL"))
    RepositorioRecurso(sesion_db).agregar(
        Recurso(
            codigo="AULA-6A",
            nombre="Aula 6A",
            tipo_recurso="GENERAL",
            capacidad=30,
            curso_titular_id=curso.id,
        )
    )

    recursos = cliente.get("/api/recursos").json()
    assert recursos[0]["curso_titular_id"] == str(curso.id)
    assert cliente.get("/api/asignaciones", params={"curso_id": str(curso.id)}).json() == []


# --- entrada manual de datos (no todo viene del Excel) -------------------------------


def test_bloque_de_recreo_se_crea_con_duracion_derivada(cliente: TestClient) -> None:
    """Un colegio sin Excel necesita poder cargar sus recreos a mano."""
    respuesta = cliente.post(
        "/api/bloques",
        json={
            "codigo": "R1",
            "orden": 2,
            "inicio": "08:00:00",
            "fin": "08:20:00",
            "tipo": "descanso",
        },
    )

    assert respuesta.status_code == 201, respuesta.text
    assert respuesta.json()["duracion_min"] == 20
    assert respuesta.json()["tipo"] == "descanso"


def test_bloque_con_duracion_inconsistente_da_400(cliente: TestClient) -> None:
    respuesta = cliente.post(
        "/api/bloques",
        json={
            "codigo": "B9",
            "orden": 9,
            "inicio": "09:00:00",
            "fin": "10:00:00",
            "duracion_min": 45,
        },
    )

    assert respuesta.status_code == 400
    assert respuesta.json()["codigo"] == "DURACION_INCONSISTENTE"


def test_bloque_con_fin_antes_del_inicio_da_400(cliente: TestClient) -> None:
    respuesta = cliente.post(
        "/api/bloques",
        json={"codigo": "B8", "orden": 8, "inicio": "10:00:00", "fin": "09:00:00"},
    )

    assert respuesta.status_code == 400
    assert respuesta.json()["codigo"] == "BLOQUE_INVALIDO"


def test_bloque_sin_uso_se_borra(cliente: TestClient) -> None:
    creado = cliente.post(
        "/api/bloques",
        json={"codigo": "B7", "orden": 7, "inicio": "11:00:00", "fin": "12:00:00"},
    ).json()

    assert cliente.delete(f"/api/bloques/{creado['id']}").status_code == 204


def test_grado_y_asignatura_se_crean_para_entrada_manual(cliente: TestClient) -> None:
    grado = cliente.post("/api/grados", json={"nombre": "8vo", "orden": 8})
    assert grado.status_code == 201

    asignatura = cliente.post(
        "/api/asignaturas", json={"nombre": "Física", "color": "#334455", "es_pesada": True}
    )
    assert asignatura.status_code == 201
    assert asignatura.json()["es_pesada"] is True

    duplicada = cliente.post(
        "/api/asignaturas", json={"nombre": "Física", "color": "#334455"}
    )
    assert duplicada.status_code == 409
    assert duplicada.json()["codigo"] == "NOMBRE_DUPLICADO"


def test_crear_curso_con_un_grado_creado_a_mano(cliente: TestClient) -> None:
    grado = cliente.post("/api/grados", json={"nombre": "8vo", "orden": 8}).json()

    curso = cliente.post(
        "/api/cursos",
        json={"codigo": "8A", "nombre": "Octavo A", "grado_id": grado["id"], "estudiantes": 25},
    )

    assert curso.status_code == 201, curso.text


def test_tipo_de_recurso_se_crea_sin_excel(cliente: TestClient) -> None:
    creado = cliente.post("/api/tipos-recurso", json={"codigo": "LAB_QUIMICA"})
    assert creado.status_code == 201
    assert cliente.post("/api/tipos-recurso", json={"codigo": "LAB_QUIMICA"}).status_code == 409

    recurso = cliente.post(
        "/api/recursos",
        json={
            "codigo": "LQ1",
            "nombre": "Laboratorio de Química",
            "tipo_recurso": "LAB_QUIMICA",
            "capacidad": 24,
        },
    )
    assert recurso.status_code == 201, recurso.text


def test_aptitud_se_crea_y_se_borra(cliente: TestClient, curso: Curso, sesion_db: Session) -> None:
    docente = RepositorioDocente(sesion_db).agregar(
        Docente(codigo="D7", nombre="Nuevo", max_sesiones_semana=20)
    )
    asignatura = RepositorioAsignatura(sesion_db).agregar(
        Asignatura(nombre="Química", color="#445566")
    )
    cuerpo = {"docente_id": str(docente.id), "asignatura_id": str(asignatura.id)}

    creada = cliente.post("/api/aptitudes", json=cuerpo)
    assert creada.status_code == 201, creada.text
    assert cliente.post("/api/aptitudes", json=cuerpo).status_code == 409

    borrada = cliente.delete(f"/api/aptitudes/{docente.id}/{asignatura.id}")
    assert borrada.status_code == 204
    assert cliente.get("/api/aptitudes").json() == []


def test_aptitud_con_docente_inexistente_da_400(cliente: TestClient, curso: Curso) -> None:
    respuesta = cliente.post(
        "/api/aptitudes",
        json={
            "docente_id": "00000000-0000-0000-0000-000000000000",
            "asignatura_id": "00000000-0000-0000-0000-000000000001",
        },
    )

    assert respuesta.status_code == 400
    assert respuesta.json()["codigo"] == "REFERENCIA_INVALIDA"
