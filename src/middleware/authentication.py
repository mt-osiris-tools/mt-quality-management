from __future__ import annotations

from typing import Any, Iterable

import structlog
from jose import JWTError
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from src.utils.security import decode_jwt_token, validate_token_claims

logger = structlog.get_logger()


def _is_public_path(
    path: str, public_paths: set[str], public_prefixes: Iterable[str]
) -> bool:
    if path in public_paths:
        return True
    return any(path.startswith(prefix) for prefix in public_prefixes)


class AuthenticationMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app: Any,
        api_prefix: str = "/api/v1",
        public_paths: set[str] | None = None,
        public_prefixes: Iterable[str] | None = None,
    ) -> None:
        super().__init__(app)
        self.api_prefix = api_prefix
        self.public_paths = public_paths or {"/health", "/ready"}
        self.public_prefixes = tuple(
            public_prefixes
            or (
                f"{api_prefix}/docs",
                f"{api_prefix}/openapi.json",
                f"{api_prefix}/redoc",
            )
        )

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        path = request.url.path
        if _is_public_path(path, self.public_paths, self.public_prefixes):
            return await call_next(request)

        if not path.startswith(self.api_prefix):
            return await call_next(request)

        auth_header = request.headers.get("authorization")
        if not auth_header:
            return JSONResponse(
                status_code=401, content={"detail": "Missing Authorization header"}
            )

        parts = auth_header.split(" ", 1)
        if len(parts) != 2 or parts[0].lower() != "bearer" or not parts[1].strip():
            return JSONResponse(
                status_code=401, content={"detail": "Invalid Authorization header"}
            )

        token = parts[1].strip()
        try:
            payload = decode_jwt_token(token)
        except JWTError as e:
            logger.warning("jwt_decode_failed", error=str(e))
            return JSONResponse(status_code=401, content={"detail": "Invalid token"})

        if not validate_token_claims(payload):
            return JSONResponse(
                status_code=401, content={"detail": "Invalid token claims"}
            )

        request.state.user = payload
        return await call_next(request)
