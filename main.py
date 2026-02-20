"""
Document Control Process - Main Application Entry Point

FastAPI application with:
- Health check endpoints (/health, /ready)
- API versioning (/api/v1)
- Security middleware (authentication, authorization, audit logging)
- CORS configuration
- Structured logging
"""

import structlog
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from src.utils.config import get_settings
from src.utils.database import get_engine

# Initialize structured logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer(),
    ],
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Get application settings
settings = get_settings()

# Create FastAPI application
app = FastAPI(
    title=settings.api_title,
    description=settings.api_description,
    version=settings.app_version,
    docs_url=f"{settings.api_prefix}/docs",
    redoc_url=f"{settings.api_prefix}/redoc",
    openapi_url=f"{settings.api_prefix}/openapi.json",
)

# Configure CORS (development only)
if settings.app_env == "development":
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=settings.cors_credentials,
        allow_methods=settings.cors_methods,
        allow_headers=settings.cors_headers,
    )


# ============================================
# Middleware (will be added in T027-T031)
# ============================================

# TODO: Add authentication middleware (T028)
# TODO: Add authorization middleware (T029)
# TODO: Add audit logging middleware (T030)


# ============================================
# Health Check Endpoints
# ============================================


@app.get("/health", tags=["health"], status_code=status.HTTP_200_OK)
async def health_check() -> dict:
    """
    Liveness probe - is the application running?

    Used by Docker health checks and orchestration systems.
    Returns 200 OK if application is alive.

    Returns:
        dict: Health status
    """
    return {
        "status": "healthy",
        "service": "document-control-api",
        "version": settings.app_version,
    }


@app.get("/ready", tags=["health"], status_code=status.HTTP_200_OK)
async def readiness_check() -> JSONResponse:
    """
    Readiness probe - can the application serve traffic?

    Checks database connection to ensure system is ready.
    Returns 200 OK if ready, 503 Service Unavailable if not.

    Returns:
        dict: Readiness status with component health
    """
    components = {"application": "ready", "database": "unknown"}

    # Check database connection
    try:
        engine = get_engine()
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        components["database"] = "connected"
        overall_status = "ready"
        status_code = status.HTTP_200_OK
    except Exception as e:
        components["database"] = f"disconnected: {str(e)}"
        overall_status = "not_ready"
        status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        logger.error("database_connection_failed", error=str(e))

    return JSONResponse(
        status_code=status_code,
        content={
            "status": overall_status,
            "components": components,
            "service": "document-control-api",
            "version": settings.app_version,
        },
    )


# ============================================
# API Routes (will be registered in T031, T056, T067, T091, T101)
# ============================================

# TODO: Register documents router (T056)
# TODO: Register search router (T067)
# TODO: Register versions router (T091)
# TODO: Register classifications router (T076)
# TODO: Register audit router (T101)


# ============================================
# Application Startup & Shutdown
# ============================================


@app.on_event("startup")
async def startup_event():
    """Application startup tasks."""
    logger.info(
        "application_starting",
        env=settings.app_env,
        version=settings.app_version,
    )


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown tasks."""
    logger.info("application_shutting_down")


# ============================================
# Exception Handlers
# ============================================


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler for unhandled errors.

    Logs error details and returns generic error response.
    Prevents sensitive information leakage in error messages.
    """
    logger.error(
        "unhandled_exception",
        error=str(exc),
        path=request.url.path,
        method=request.method,
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "INTERNAL_SERVER_ERROR",
            "message": "An internal error occurred. Please contact support.",
        },
    )


# ============================================
# Application Entry Point
# ============================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True if settings.app_env == "development" else False,
        log_level=settings.log_level.lower(),
    )
