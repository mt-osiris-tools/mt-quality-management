import os

import pytest
from jose import JWTError, jwt

from src.utils.config import get_settings
from src.utils.security import (
    create_mock_jwt_token,
    decode_jwt_token,
    generate_hash,
    get_role_hierarchy_level,
    has_role_access,
    hash_password,
    validate_token_claims,
    verify_hash,
    verify_password,
)


def test_hash_helpers() -> None:
    h = generate_hash("a", 1, "b")
    assert len(h) == 64
    assert verify_hash("data", generate_hash("data"))
    assert not verify_hash("data", generate_hash("other"))


def test_password_hashing() -> None:
    hashed = hash_password("S0m3Str0ngP@ssw0rd")
    assert verify_password("S0m3Str0ngP@ssw0rd", hashed)
    assert not verify_password("wrong", hashed)


def test_validate_token_claims() -> None:
    assert validate_token_claims(
        {
            "sub": "1",
            "email": "user@example.com",
            "role": "Editor",
            "classification_clearance": 2,
        }
    )
    assert not validate_token_claims({"sub": "1"})
    assert not validate_token_claims(
        {
            "sub": "1",
            "email": "user@example.com",
            "role": "Invalid",
            "classification_clearance": 2,
        }
    )
    assert not validate_token_claims(
        {
            "sub": "1",
            "email": "user@example.com",
            "role": "Editor",
            "classification_clearance": 99,
        }
    )


def test_role_hierarchy_and_access() -> None:
    assert get_role_hierarchy_level("Admin") > get_role_hierarchy_level("Viewer")
    assert has_role_access("Admin", "Manager")
    assert has_role_access("Manager", "Editor")
    assert not has_role_access("Viewer", "Editor")

    assert has_role_access("Auditor", "Auditor")
    assert not has_role_access("Auditor", "Viewer")


def test_create_mock_jwt_token_is_decodable() -> None:
    token = create_mock_jwt_token(
        user_id=1,
        email="user@example.com",
        role="Viewer",
        classification_clearance=1,
        expires_minutes=5,
    )
    payload = jwt.decode(
        token,
        os.environ["DEV_JWT_SECRET"],
        algorithms=["HS256"],
    )
    assert payload["role"] == "Viewer"


def test_decode_jwt_token_success_with_generated_rs256_keypair() -> None:
    pytest.importorskip("cryptography")
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import rsa

    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_key = private_key.public_key()

    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode("ascii")
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode("ascii")

    old_public_key = os.environ.get("JWT_PUBLIC_KEY")
    old_algorithm = os.environ.get("JWT_ALGORITHM")

    os.environ["JWT_PUBLIC_KEY"] = public_pem
    os.environ["JWT_ALGORITHM"] = "RS256"
    get_settings.cache_clear()

    token = jwt.encode(
        {
            "sub": "1",
            "email": "user@example.com",
            "role": "Editor",
            "classification_clearance": 2,
        },
        private_pem,
        algorithm="RS256",
    )

    payload = decode_jwt_token(token)
    assert payload["sub"] == "1"

    if old_public_key is None:
        del os.environ["JWT_PUBLIC_KEY"]
    else:
        os.environ["JWT_PUBLIC_KEY"] = old_public_key

    if old_algorithm is None:
        os.environ.pop("JWT_ALGORITHM", None)
    else:
        os.environ["JWT_ALGORITHM"] = old_algorithm

    get_settings.cache_clear()


def test_decode_jwt_token_invalid_raises() -> None:
    with pytest.raises(JWTError):
        decode_jwt_token("not-a-jwt")
