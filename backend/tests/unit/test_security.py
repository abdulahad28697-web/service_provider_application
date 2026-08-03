"""Unit tests for security primitives (password hashing and JWT)."""
from datetime import timedelta

import jwt
import pytest

from app.common.constants import UserRole
from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


def test_hash_and_verify_password_roundtrip():
    hashed = hash_password("s3cret!")
    assert hashed != "s3cret!"
    assert verify_password("s3cret!", hashed) is True


def test_verify_password_wrong_plaintext_fails():
    hashed = hash_password("correct")
    assert verify_password("wrong", hashed) is False


def test_create_and_decode_token_roundtrip():
    token = create_access_token(subject="42", role=UserRole.ADMIN.value)
    payload = decode_access_token(token)
    assert payload["sub"] == "42"
    assert payload["role"] == UserRole.ADMIN.value


def test_expired_token_is_rejected():
    token = create_access_token(
        subject="1", expires_delta=timedelta(seconds=-1)
    )
    with pytest.raises(jwt.ExpiredSignatureError):
        decode_access_token(token)
