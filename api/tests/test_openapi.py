"""`docs/openapi.json` no puede quedar atrás de la API.

La fase 5 lo generó y para la fase 9 le faltaban tres endpoints (reglas y escenario). Este
test es el que lo hubiera detectado: compara los paths publicados contra la app real.
"""

import json
from pathlib import Path

from app.main import app

ARCHIVO = Path(__file__).resolve().parents[2] / "docs" / "openapi.json"


def _operaciones(esquema: dict) -> set[str]:
    return {
        f"{metodo.upper()} {ruta}"
        for ruta, operaciones in esquema["paths"].items()
        for metodo in operaciones
    }


def test_openapi_documenta_todas_las_rutas() -> None:
    publicado = _operaciones(json.loads(ARCHIVO.read_text(encoding="utf-8")))
    real = _operaciones(app.openapi())

    faltantes = sorted(real - publicado)

    assert not faltantes, (
        "docs/openapi.json está atrás. Regeneralo con "
        "`uv run --directory api python scripts/exportar_openapi.py`. Falta: "
        + ", ".join(faltantes)
    )
