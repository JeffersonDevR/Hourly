"""Configuración por entorno (12-factor).

El default de `database_url` es SQLite en archivo (D-001). Volver a Postgres es
cambiar `DATABASE_URL`, sin tocar código.

Los `.env` se resuelven por ruta absoluta, no por cwd: el resultado es el mismo
se ejecute `uvicorn` desde la raíz del repo o desde `api/`.
"""

from functools import lru_cache
from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

API_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = API_DIR.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        # El .env de la raíz es el documentado en `.env.example`; el de api/ gana si existe.
        env_file=(REPO_ROOT / ".env", API_DIR / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    database_url: str = "sqlite:///./hourly.db"

    # Asistente IA: API compatible con OpenAI (D-002). Vacío => NullProvider.
    ai_base_url: str | None = None
    ai_model: str | None = None
    ai_api_key: str | None = None

    # Timeout del solver CP-SAT, en segundos (ARCHITECTURE.md).
    solver_timeout_s: float = 20.0

    @field_validator("ai_base_url", "ai_model", "ai_api_key", mode="before")
    @classmethod
    def vacio_es_none(cls, valor: object) -> object:
        """`AI_API_KEY=` en el .env significa "sin IA", no la cadena vacía."""
        if isinstance(valor, str) and not valor.strip():
            return None
        return valor


@lru_cache
def get_settings() -> Settings:
    return Settings()
