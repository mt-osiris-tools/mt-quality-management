from __future__ import annotations

import hashlib
import hmac
import json
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from src.models.audit_log import AuditLog
from src.utils.config import get_settings


def _canonical_json(value: object) -> str:
    return json.dumps(value, separators=(",", ":"), sort_keys=True, ensure_ascii=True)


def _compute_audit_hmac(
    key: str, previous_hash: str | None, payload: dict[str, Any]
) -> str:
    message = f"{previous_hash or ''}|{_canonical_json(payload)}".encode("utf-8")
    mac = hmac.new(key.encode("utf-8"), message, hashlib.sha256)
    return mac.hexdigest()


def _get_previous_hash(db: Session) -> str | None:
    row = db.query(AuditLog.current_hash).order_by(AuditLog.id.desc()).limit(1).first()
    if not row:
        return None
    return row[0]


def create_audit_log(
    db: Session,
    *,
    event_type: str,
    actor_id: int,
    actor_role: str,
    actor_email: str | None = None,
    actor_clearance: int | None = None,
    resource_type: str,
    action: str,
    resource_id: int | None = None,
    classification_level: int | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
    details: dict[str, Any] | None = None,
) -> AuditLog:
    settings = get_settings()

    if db.bind is not None and db.bind.dialect.name == "postgresql":
        db.execute(text("SELECT pg_advisory_xact_lock(424242)"))

    if actor_email is not None and actor_clearance is not None:
        db.execute(
            text(
                """
                INSERT INTO users (id, email, role, classification_clearance, active)
                VALUES (:id, :email, :role, :classification_clearance, true)
                ON CONFLICT (id) DO UPDATE SET
                    email = excluded.email,
                    role = excluded.role,
                    classification_clearance = excluded.classification_clearance,
                    active = true
                """
            ),
            {
                "id": actor_id,
                "email": actor_email,
                "role": actor_role,
                "classification_clearance": actor_clearance,
            },
        )

    previous_hash = _get_previous_hash(db)
    timestamp = datetime.now(timezone.utc)

    payload = {
        "timestamp": timestamp.isoformat(),
        "event_type": event_type,
        "actor_id": actor_id,
        "actor_role": actor_role,
        "resource_type": resource_type,
        "resource_id": resource_id,
        "action": action,
        "classification_level": classification_level,
        "ip_address": ip_address,
        "user_agent": user_agent,
        "details": details or {},
    }

    current_hash = _compute_audit_hmac(settings.audit_hmac_key, previous_hash, payload)

    entry = AuditLog(
        timestamp=timestamp,
        event_type=event_type,
        actor_id=actor_id,
        actor_role=actor_role,
        resource_type=resource_type,
        resource_id=resource_id,
        action=action,
        classification_level=classification_level,
        ip_address=ip_address,
        user_agent=user_agent,
        details=details,
        previous_hash=previous_hash,
        current_hash=current_hash,
    )
    db.add(entry)
    db.flush()
    return entry
