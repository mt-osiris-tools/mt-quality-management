"""
Database connection and session management.

Provides SQLAlchemy engine, session maker, and Base class for ORM models.
Implements connection pooling for 100 concurrent users as per performance requirements.
"""

from contextlib import contextmanager
from typing import Any, Generator, Mapping, Protocol

from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker
from sqlalchemy.pool import QueuePool, StaticPool

from src.utils.config import get_settings

# Declarative Base for ORM models
Base = declarative_base()

# Global engine and session maker (initialized on first use)
_engine: Engine | None = None
_SessionLocal: sessionmaker | None = None


def get_engine() -> Engine:
    """
    Get or create SQLAlchemy engine with connection pooling.

    Connection pool configured for 100 concurrent users:
    - pool_size: 10 connections
    - max_overflow: 20 additional connections
    - pool_timeout: 30 seconds

    Returns:
        Engine: SQLAlchemy database engine
    """
    global _engine
    if _engine is None:
        settings = get_settings()
        database_url = settings.database_url

        engine_kwargs: dict[str, object] = {
            "pool_pre_ping": True,
            "echo": settings.db_echo,
        }

        if database_url.startswith("sqlite"):
            engine_kwargs["connect_args"] = {"check_same_thread": False}
            if ":memory:" in database_url:
                engine_kwargs["poolclass"] = StaticPool
        else:
            engine_kwargs["poolclass"] = QueuePool
            engine_kwargs["pool_size"] = settings.db_pool_size
            engine_kwargs["max_overflow"] = settings.db_max_overflow
            engine_kwargs["pool_timeout"] = settings.db_pool_timeout

        _engine = create_engine(database_url, **engine_kwargs)

        # Enable Row-Level Security context for all connections
        @event.listens_for(_engine, "connect")
        def set_session_context(dbapi_conn, connection_record):
            """Set session context variables for Row-Level Security."""
            # Context will be set per-request in middleware
            # This is a placeholder for the connection event
            pass

    return _engine


def get_session_maker() -> sessionmaker:
    """
    Get or create SQLAlchemy session maker.

    Returns:
        sessionmaker: Session factory for database operations
    """
    global _SessionLocal
    if _SessionLocal is None:
        engine = get_engine()
        _SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=engine,
            expire_on_commit=False,
        )
    return _SessionLocal


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency for database sessions.

    Yields a database session and ensures proper cleanup.
    Use as: db: Session = Depends(get_db)

    Yields:
        Session: Database session
    """
    SessionLocal = get_session_maker()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_context() -> Generator[Session, None, None]:
    """
    Context manager for database sessions in non-FastAPI contexts.

    Usage:
        with get_db_context() as db:
            # Use db session
            user = db.query(User).first()

    Yields:
        Session: Database session
    """
    SessionLocal = get_session_maker()
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


class _SupportsExecute(Protocol):
    def execute(
        self, statement: Any, params: Mapping[str, Any] | None = None
    ) -> Any: ...


def set_rls_context(db: _SupportsExecute, user_id: int, user_role: str) -> None:
    db.execute(
        text("SELECT set_config('app.user_id', :user_id, true)"),
        {"user_id": str(user_id)},
    )
    db.execute(
        text("SELECT set_config('app.user_role', :user_role, true)"),
        {"user_role": user_role},
    )


def init_db() -> None:
    """
    Initialize database schema.

    Creates all tables defined in Base.metadata.
    Note: In production, use Alembic migrations instead.
    """
    import importlib

    importlib.import_module("src.models")

    engine = get_engine()
    Base.metadata.create_all(bind=engine)


def drop_db() -> None:
    """
    Drop all database tables.

    WARNING: This is destructive! Use only for testing.
    """
    engine = get_engine()
    Base.metadata.drop_all(bind=engine)
