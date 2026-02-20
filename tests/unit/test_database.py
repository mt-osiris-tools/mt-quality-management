from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sqlalchemy import text
from sqlalchemy.engine import Engine

from src.utils.database import (
    drop_db,
    get_db,
    get_db_context,
    get_engine,
    get_session_maker,
    init_db,
    set_rls_context,
)


def test_engine_and_session_maker() -> None:
    engine = get_engine()
    assert isinstance(engine, Engine)

    SessionLocal = get_session_maker()
    db = SessionLocal()
    db.close()


def test_get_db_generator_closes_session() -> None:
    gen = get_db()
    db = next(gen)
    db.close()
    gen.close()


def test_db_context_manager_commits() -> None:
    with get_db_context() as db:
        db.execute(text("SELECT 1"))


def test_init_and_drop_db_no_tables() -> None:
    init_db()
    drop_db()


@dataclass
class _Call:
    statement: Any
    params: dict[str, Any]


class _FakeSession:
    def __init__(self) -> None:
        self.calls: list[_Call] = []

    def execute(self, statement: Any, params: dict[str, Any]) -> None:
        self.calls.append(_Call(statement=statement, params=params))


def test_set_rls_context_uses_set_config() -> None:
    db = _FakeSession()
    set_rls_context(db, user_id=123, user_role="Admin")

    assert len(db.calls) == 2
    assert "set_config" in str(db.calls[0].statement)
    assert db.calls[0].params["user_id"] == "123"
    assert db.calls[1].params["user_role"] == "Admin"
