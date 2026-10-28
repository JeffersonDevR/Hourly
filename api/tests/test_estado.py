from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_estado_devuelve_ok_y_ia_no_disponible() -> None:
    respuesta = client.get("/api/estado")

    assert respuesta.status_code == 200
    assert respuesta.json() == {"ok": True, "ai_disponible": False}


def test_estado_es_json() -> None:
    respuesta = client.get("/api/estado")

    assert respuesta.headers["content-type"] == "application/json"
