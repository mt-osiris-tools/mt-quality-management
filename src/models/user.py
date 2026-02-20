from __future__ import annotations

from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from src.utils.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(sa.Integer(), primary_key=True)
    email: Mapped[str] = mapped_column(sa.String(length=255), unique=True)
    role: Mapped[str] = mapped_column(sa.String(length=20))
    classification_clearance: Mapped[int] = mapped_column(
        sa.Integer(), server_default=sa.text("1")
    )
    active: Mapped[bool] = mapped_column(sa.Boolean(), server_default=sa.text("true"))
    last_login: Mapped[datetime | None] = mapped_column(
        sa.DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")
    )
    updated_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")
    )
