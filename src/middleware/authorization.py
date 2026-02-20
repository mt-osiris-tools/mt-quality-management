from __future__ import annotations

from typing import Any

from fastapi import Depends, HTTPException, Request, status

from src.utils.security import has_role_access


def get_current_user(request: Request) -> dict[str, Any]:
    user = getattr(request.state, "user", None)
    if not isinstance(user, dict):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated"
        )
    return user


def require_role(required_role: str):
    def _dep(user: dict[str, Any] = Depends(get_current_user)) -> dict[str, Any]:
        user_role = user.get("role")
        if not isinstance(user_role, str) or not has_role_access(
            user_role, required_role
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions"
            )
        return user

    return _dep


def require_clearance(min_clearance: int):
    def _dep(user: dict[str, Any] = Depends(get_current_user)) -> dict[str, Any]:
        clearance = user.get("classification_clearance")
        if not isinstance(clearance, int) or clearance < min_clearance:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient clearance"
            )
        return user

    return _dep
