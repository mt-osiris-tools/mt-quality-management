"""
Security utilities for hashing, token validation, and cryptographic operations.

Implements security helpers for:
- SHA-256 hash generation (audit log checksums)
- JWT token validation and claim extraction
- Password hashing (if needed for future user management)
"""

import hashlib
import os
from datetime import datetime, timedelta
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from src.utils.config import get_settings

# Password hashing context (bcrypt)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def generate_hash(*values: Any) -> str:
    """
    Generate SHA-256 hash from multiple values.

    Used for audit log checksum chain generation.
    Concatenates all values and returns hex-encoded hash.

    Args:
        *values: Values to hash (converted to strings)

    Returns:
        str: Hex-encoded SHA-256 hash
    """
    concatenated = "".join(str(v) for v in values)
    return hashlib.sha256(concatenated.encode()).hexdigest()


def verify_hash(data: str, expected_hash: str) -> bool:
    """
    Verify data matches expected hash.

    Args:
        data: Data to hash
        expected_hash: Expected hash value

    Returns:
        bool: True if hash matches
    """
    actual_hash = hashlib.sha256(data.encode()).hexdigest()
    return actual_hash == expected_hash


def hash_password(password: str) -> str:
    """
    Hash password using bcrypt.

    Note: Password complexity requirements per constitution:
    - Minimum 12 characters
    - Mixed case letters
    - Numbers
    - Symbols

    Args:
        password: Plain text password

    Returns:
        str: Hashed password
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify password against hash.

    Args:
        plain_password: Plain text password
        hashed_password: Hashed password from database

    Returns:
        bool: True if password matches
    """
    return pwd_context.verify(plain_password, hashed_password)


def decode_jwt_token(token: str) -> dict[str, Any]:
    """
    Decode and validate JWT token.

    Validates token signature using public key from external IdP.
    Extracts claims: sub, email, role, classification_clearance

    Args:
        token: JWT token string

    Returns:
        Dict[str, Any]: Token payload with claims

    Raises:
        JWTError: If token is invalid or expired
    """
    settings = get_settings()

    try:
        payload = jwt.decode(
            token,
            settings.jwt_public_key,
            algorithms=[settings.jwt_algorithm],
            audience=settings.jwt_audience,
            issuer=settings.jwt_issuer,
        )
        return payload
    except JWTError as e:
        raise JWTError(f"Invalid token: {str(e)}")


def validate_token_claims(payload: dict[str, Any]) -> bool:
    """
    Validate required JWT token claims are present.

    Required claims per specification:
    - sub: User ID
    - email: User email
    - role: One of [Admin, Manager, Editor, Viewer, Auditor]
    - classification_clearance: Integer 0-3

    Args:
        payload: Decoded JWT payload

    Returns:
        bool: True if all required claims present and valid
    """
    required_claims = ["sub", "email", "role", "classification_clearance"]

    # Check all required claims present
    if not all(claim in payload for claim in required_claims):
        return False

    # Validate role
    valid_roles = ["Admin", "Manager", "Editor", "Viewer", "Auditor"]
    if payload.get("role") not in valid_roles:
        return False

    # Validate classification clearance
    clearance = payload.get("classification_clearance")
    if not isinstance(clearance, int) or not (0 <= clearance <= 3):
        return False

    return True


def get_role_hierarchy_level(role: str) -> int:
    """
    Get numeric hierarchy level for role.

    Role hierarchy (higher number = more permissions):
    - Admin: 4 (full access)
    - Manager: 3 (document CRUD + classification management)
    - Editor: 2 (create and modify own documents)
    - Viewer: 1 (read-only)
    - Auditor: 0 (special role, read + audit log access)

    Args:
        role: User role

    Returns:
        int: Hierarchy level (0-4)
    """
    hierarchy = {
        "Admin": 4,
        "Manager": 3,
        "Editor": 2,
        "Viewer": 1,
        "Auditor": 0,  # Special role with specific permissions
    }
    return hierarchy.get(role, 0)


def has_role_access(user_role: str, required_role: str) -> bool:
    """
    Check if user role has sufficient access for required role.

    Special handling for Auditor role:
    - Auditors only have access to Auditor-specific endpoints
    - Auditors cannot perform document CRUD operations

    Args:
        user_role: User's current role
        required_role: Required role for operation

    Returns:
        bool: True if user has sufficient access
    """
    # Special case: Auditor role has specific permissions only
    if user_role == "Auditor":
        return required_role == "Auditor"

    # Check role hierarchy for other roles
    user_level = get_role_hierarchy_level(user_role)
    required_level = get_role_hierarchy_level(required_role)

    return user_level >= required_level


def create_mock_jwt_token(
    user_id: int,
    email: str,
    role: str,
    classification_clearance: int,
    expires_minutes: int = 30,
) -> str:
    """
    Create mock JWT token for development/testing.

    WARNING: This is for development/testing only.
    In production, tokens are issued by an external IdP.

    Args:
        user_id: User ID
        email: User email
        role: User role
        classification_clearance: Classification clearance level (0-3)
        expires_minutes: Token expiration in minutes

    Returns:
        str: JWT token string
    """
    payload = {
        "sub": str(user_id),
        "email": email,
        "role": role,
        "classification_clearance": classification_clearance,
        "iat": datetime.utcnow(),
        "exp": datetime.utcnow() + timedelta(minutes=expires_minutes),
    }

    secret_key = os.getenv("DEV_JWT_SECRET")
    if not secret_key:
        raise RuntimeError("DEV_JWT_SECRET is required for mock token generation")

    return jwt.encode(payload, secret_key, algorithm="HS256")
