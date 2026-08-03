"""Unit tests for the auth service (registration, login, tokens)."""
import pytest
from pydantic import ValidationError

from app.core.exceptions import ConflictError, UnauthorizedError
from app.core.security import decode_access_token, verify_password
from app.schemas.auth import UserRegister
from app.services.auth_service import AuthService
from tests import factories


@pytest.fixture
async def svc(db):
    return AuthService(db)


async def test_register_hashes_password_and_sets_role(svc, db):
    user = await svc.register(
        UserRegister(email="new@example.com", full_name="New User", password="Passw0rd!")
    )
    assert user.id is not None
    assert user.role.value == "customer"
    assert verify_password("Passw0rd!", user.hashed_password)


async def test_register_duplicate_email_conflict(svc, db):
    await factories.make_user(db, email="dup@example.com", password="Passw0rd!")
    with pytest.raises(ConflictError):
        await svc.register(
            UserRegister(email="dup@example.com", full_name="Dup", password="Passw0rd!")
        )


async def test_register_weak_password_rejected():
    with pytest.raises(ValidationError):
        UserRegister(email="a@example.com", full_name="A", password="short")


async def test_authenticate_success(svc, db):
    await svc.register(
        UserRegister(email="ok@example.com", full_name="Ok", password="Passw0rd!")
    )
    user = await svc.authenticate("ok@example.com", "Passw0rd!")
    assert user.email == "ok@example.com"


async def test_authenticate_wrong_password_unauthorized(svc, db):
    await svc.register(
        UserRegister(email="ok@example.com", full_name="Ok", password="Passw0rd!")
    )
    with pytest.raises(UnauthorizedError):
        await svc.authenticate("ok@example.com", "WrongPass1")


async def test_authenticate_inactive_user_unauthorized(svc, db):
    user = await svc.register(
        UserRegister(email="inactive@example.com", full_name="In", password="Passw0rd!")
    )
    user.is_active = False
    await db.flush()
    with pytest.raises(UnauthorizedError):
        await svc.authenticate("inactive@example.com", "Passw0rd!")


async def test_issue_token_decodes(svc, db):
    user = await factories.make_user(db)
    token = svc.issue_token(user)
    payload = decode_access_token(token)
    assert payload["sub"] == str(user.id)
