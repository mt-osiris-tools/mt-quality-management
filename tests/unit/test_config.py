import os

import pytest
from pydantic import ValidationError

from src.utils.config import Settings, get_settings


def test_get_settings_loads_env() -> None:
    get_settings.cache_clear()
    settings = get_settings()
    assert settings.database_url
    assert settings.jwt_public_key
    assert settings.encryption_key_level_1


def test_settings_missing_required_value_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    original = os.environ.get("DATABASE_URL")
    monkeypatch.setenv("DATABASE_URL", "")
    get_settings.cache_clear()

    with pytest.raises(ValidationError):
        Settings()

    if original is None:
        monkeypatch.delenv("DATABASE_URL", raising=False)
    else:
        monkeypatch.setenv("DATABASE_URL", original)
    get_settings.cache_clear()
