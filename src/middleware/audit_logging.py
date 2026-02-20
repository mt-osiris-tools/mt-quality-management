from __future__ import annotations

import time

import structlog
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from src.services.audit_service import create_audit_log
from src.utils.config import get_settings
from src.utils.database import get_db_context

logger = structlog.get_logger()


def _event_type(method: str) -> str:
    if method == "POST":
        return "CREATE"
    if method == "PUT" or method == "PATCH":
        return "UPDATE"
    if method == "DELETE":
        return "DELETE"
    return "READ"


def _ip_address(request: Request) -> str | None:
    if request.client is None:
        return None
    return request.client.host


class AuditLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = int((time.perf_counter() - start) * 1000)

        settings = get_settings()
        path = request.url.path
        if not path.startswith(settings.api_prefix):
            return response

        user = getattr(request.state, "user", None)
        if not isinstance(user, dict):
            return response

        actor_role = user.get("role")
        sub = user.get("sub")
        email = user.get("email")
        clearance = user.get("classification_clearance")
        if (
            not isinstance(actor_role, str)
            or not isinstance(sub, str)
            or not sub.isdigit()
        ):
            return response

        actor_id = int(sub)
        if not isinstance(email, str) or not isinstance(clearance, int):
            return response

        details = {
            "path": path,
            "status_code": response.status_code,
            "duration_ms": duration_ms,
            "query": request.url.query,
        }

        try:
            with get_db_context() as db:
                create_audit_log(
                    db,
                    event_type=_event_type(request.method),
                    actor_id=actor_id,
                    actor_role=actor_role,
                    actor_email=email,
                    actor_clearance=clearance,
                    resource_type="HTTP",
                    resource_id=None,
                    action=f"HTTP_{request.method}",
                    classification_level=clearance,
                    ip_address=_ip_address(request),
                    user_agent=request.headers.get("user-agent"),
                    details={"user": {"email": email}, **details},
                )
        except Exception as e:
            logger.error("audit_log_persist_failed", error=str(e), path=path)

        user = getattr(request.state, "user", None)
        log_actor_id = None
        log_actor_role = None
        if isinstance(user, dict):
            log_actor_id = user.get("sub")
            log_actor_role = user.get("role")

        logger.info(
            "http_request",
            method=request.method,
            path=path,
            status_code=response.status_code,
            duration_ms=duration_ms,
            actor_id=log_actor_id,
            actor_role=log_actor_role,
        )
        return response
