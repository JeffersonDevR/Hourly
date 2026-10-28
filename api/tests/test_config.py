import pytest

from app.config import Settings, get_settings

VARIABLES = ("DATABASE_URL", "AI_BASE_URL", "AI_MODEL", "AI_API_KEY", "SOLVER_TIMEOUT_S")


@pytest.fixture
def sin_entorno(monkeypatch: pytest.MonkeyPatch) -> None:
    """Aisla el test del entorno del desarrollador y de un `.env` local."""
    for variable in VARIABLES:
        monkeypatch.delenv(variable, raising=False)


def test_defaults_documentados(sin_entorno: None) -> None:
    settings = Settings(_env_file=None)

    assert settings.database_url == "sqlite:///./hourly.db"
    assert settings.solver_timeout_s == 20.0
    assert settings.ai_base_url is None
    assert settings.ai_model is None
    assert settings.ai_api_key is None


def test_variables_de_ia_vacias_son_none(sin_entorno: None) -> None:
    settings = Settings(_env_file=None, ai_api_key="", ai_base_url="  ")

    assert settings.ai_api_key is None
    assert settings.ai_base_url is None


def test_settings_es_cacheado() -> None:
    assert get_settings() is get_settings()
