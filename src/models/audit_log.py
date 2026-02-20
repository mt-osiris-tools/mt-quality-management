from __future__ import annotations

from datetime import datetime
from typing import Any

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from src.utils.database import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(
        sa.BigInteger().with_variant(sa.Integer(), "sqlite"),
        primary_key=True,
        autoincrement=True,
    )
    timestamp: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")
    )
    event_type: Mapped[str] = mapped_column(sa.String(length=50))
    actor_id: Mapped[int] = mapped_column(sa.Integer(), sa.ForeignKey("users.id"))
    actor_role: Mapped[str] = mapped_column(sa.String(length=20))
    resource_type: Mapped[str] = mapped_column(sa.String(length=50))
    resource_id: Mapped[int | None] = mapped_column(sa.Integer(), nullable=True)
    action: Mapped[str] = mapped_column(sa.String(length=50))
    classification_level: Mapped[int | None] = mapped_column(
        sa.Integer(), nullable=True
    )

    ip_address: Mapped[str | None] = mapped_column(sa.String(length=45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(sa.Text(), nullable=True)
    details: Mapped[dict[str, Any] | None] = mapped_column(sa.JSON(), nullable=True)

    previous_hash: Mapped[str | None] = mapped_column(
        sa.String(length=64), nullable=True
    )
    current_hash: Mapped[str] = mapped_column(sa.String(length=64))
