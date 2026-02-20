from __future__ import annotations

from typing import Any

import pytest
from fastapi import Depends, FastAPI, Request
from fastapi.testclient import TestClient
from jose import jwt

from src.middleware.audit_logging import AuditLoggingMiddleware
from src.middleware.authentication import AuthenticationMiddleware
from src.middleware.authorization import require_clearance, require_role
from src.models.audit_log import AuditLog
from src.utils.config import get_settings
from src.utils.database import get_db_context


def _make_app() -> FastAPI:
    app = FastAPI()
    app.add_middleware(AuditLoggingMiddleware)
    app.add_middleware(AuthenticationMiddleware, api_prefix="/api/v1")

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/api/v1/protected")
    async def protected(request: Request) -> dict[str, Any]:
        user = getattr(request.state, "user", None)
        return {"user": user}

    @app.get("/api/v1/manager", dependencies=[Depends(require_role("Manager"))])
    async def manager_only() -> dict[str, bool]:
        return {"ok": True}

    @app.get("/api/v1/clearance2", dependencies=[Depends(require_clearance(2))])
    async def clearance2_only() -> dict[str, bool]:
        return {"ok": True}

    return app


def _make_token(secret: str, role: str, clearance: int) -> str:
    return jwt.encode(
        {
            "sub": "1",
            "email": "user@example.com",
            "role": role,
            "classification_clearance": clearance,
        },
        secret,
        algorithm="HS256",
    )


def test_auth_middleware_allows_health_without_token() -> None:
    client = TestClient(_make_app())
    resp = client.get("/health")
    assert resp.status_code == 200


def test_auth_middleware_rejects_missing_token(monkeypatch: pytest.MonkeyPatch) -> None:
    secret = "test-secret"
    monkeypatch.setenv("JWT_ALGORITHM", "HS256")
    monkeypatch.setenv("JWT_PUBLIC_KEY", secret)
    get_settings.cache_clear()

    client = TestClient(_make_app())
    resp = client.get("/api/v1/protected")
    assert resp.status_code == 401


def test_auth_middleware_accepts_valid_token_and_sets_user(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    secret = "test-secret"
    monkeypatch.setenv("JWT_ALGORITHM", "HS256")
    monkeypatch.setenv("JWT_PUBLIC_KEY", secret)
    get_settings.cache_clear()

    token = _make_token(secret, role="Viewer", clearance=1)
    client = TestClient(_make_app())
    resp = client.get("/api/v1/protected", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["user"]["email"] == "user@example.com"

    with get_db_context() as db:
        assert db.query(AuditLog).count() >= 1


def test_authorization_require_role(monkeypatch: pytest.MonkeyPatch) -> None:
    secret = "test-secret"
    monkeypatch.setenv("JWT_ALGORITHM", "HS256")
    monkeypatch.setenv("JWT_PUBLIC_KEY", secret)
    get_settings.cache_clear()

    client = TestClient(_make_app())

    viewer_token = _make_token(secret, role="Viewer", clearance=1)
    resp = client.get(
        "/api/v1/manager", headers={"Authorization": f"Bearer {viewer_token}"}
    )
    assert resp.status_code == 403

    manager_token = _make_token(secret, role="Manager", clearance=2)
    resp = client.get(
        "/api/v1/manager", headers={"Authorization": f"Bearer {manager_token}"}
    )
    assert resp.status_code == 200


def test_authorization_require_clearance(monkeypatch: pytest.MonkeyPatch) -> None:
    secret = "test-secret"
    monkeypatch.setenv("JWT_ALGORITHM", "HS256")
    monkeypatch.setenv("JWT_PUBLIC_KEY", secret)
    get_settings.cache_clear()

    client = TestClient(_make_app())

    low = _make_token(secret, role="Manager", clearance=1)
    resp = client.get("/api/v1/clearance2", headers={"Authorization": f"Bearer {low}"})
    assert resp.status_code == 403

    high = _make_token(secret, role="Manager", clearance=2)
    resp = client.get("/api/v1/clearance2", headers={"Authorization": f"Bearer {high}"})
    assert resp.status_code == 200
