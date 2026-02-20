import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def pytest_configure() -> None:
    from src.utils.config import get_settings
    from src.utils.database import init_db

    os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")
    os.environ.setdefault("ENCRYPTION_KEY_LEVEL_1", "a" * 44)
    os.environ.setdefault("ENCRYPTION_KEY_LEVEL_2", "b" * 44)
    os.environ.setdefault("ENCRYPTION_KEY_LEVEL_3", "c" * 44)
    os.environ.setdefault("JWT_PUBLIC_KEY", "test-public-key")
    os.environ.setdefault("APP_ENV", "test")
    os.environ.setdefault("DEV_JWT_SECRET", "test-dev-jwt-secret")
    os.environ.setdefault("AUDIT_HMAC_KEY", "test-audit-hmac-key")

    get_settings.cache_clear()

    init_db()
