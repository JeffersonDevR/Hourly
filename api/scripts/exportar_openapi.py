"""Escribe `docs/openapi.json` desde la app, sin levantar el servidor.

`uv run --directory api python scripts/exportar_openapi.py`
"""

import json
import pathlib
import sys

# `python scripts/x.py` agrega `scripts/`, no la raíz del proyecto.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from app.main import app  # noqa: E402

DESTINO = pathlib.Path(__file__).resolve().parents[2] / "docs" / "openapi.json"


def main() -> None:
    DESTINO.write_text(
        json.dumps(app.openapi(), indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(f"{DESTINO} — {sum(len(v) for v in app.openapi()['paths'].values())} operaciones")


if __name__ == "__main__":
    main()
