"""Utilidades de DB para los tests: URL, config de Alembic y migración.

Vive fuera de `conftest.py` para poder importarse desde los tests sin duplicar el
módulo de fixtures.
"""

import os
import subprocess
import sys
from pathlib import Path

from alembic import command
from alembic.config import Config

API_DIR = Path(__file__).resolve().parents[1]


def url_sqlite(ruta: Path) -> str:
    """URL de SQLAlchemy para un archivo. `as_posix()` evita las barras invertidas de Windows."""
    return f"sqlite:///{ruta.as_posix()}"


def config_alembic(url: str) -> Config:
    """Config de Alembic apuntando a `api/`, con la URL del test."""
    config = Config(str(API_DIR / "alembic.ini"))
    config.set_main_option("script_location", str(API_DIR / "alembic"))
    config.set_main_option("sqlalchemy.url", url)
    return config


def migrar(url: str) -> None:
    command.upgrade(config_alembic(url), "head")


def migrar_por_cli(url: str) -> subprocess.CompletedProcess[str]:
    """Corre el mismo comando que el desarrollador, en un proceso aparte."""
    return subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=API_DIR,
        env={**os.environ, "DATABASE_URL": url},
        capture_output=True,
        text=True,
        check=False,
    )
