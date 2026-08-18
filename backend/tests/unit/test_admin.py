"""Unit tests for the admin + provider-onboarding services."""
import pytest
from sqlalchemy import select

from app.common.constants import UserRole
from app.core.exceptions import ConflictError, NotFoundError
from app.models.notification import Notification
from app.models.provider import Provider
from app.models.user import User
from app.schemas.admin import ProviderOnboard, ProviderVerifyRequest
from app.services.admin_service import AdminService
from app.services.provider_service import ProviderService
from tests import factories


@pytest.fixture
async def providers(db):
    return ProviderService(db)


@pytest.fixture
async def admin(db):
    return AdminService(db)


def _onboard(category: str = "Plumbing") -> ProviderOnboard:
    return ProviderOnboard(
        business_name="Ace Plumbing",
        description="Reliable plumbing services.",
        category=category,
        hourly_rate=60,
    )


async def test_onboard_creates_profile(providers, db):
    user = await factories.make_user(db, role="provider")
    provider = await providers.onboard(user, _onboard())
    assert provider.user_id == user.id
    assert provider.category == "Plumbing"
    assert provider.is_verified is False


async def test_onboard_requires_provider_role(providers, db):
    user = await factories.make_user(db, role="customer")
    with pytest.raises(NotFoundError):
        await providers.onboard(user, _onboard())


async def test_onboard_duplicate_conflict(providers, db):
    user = await factories.make_user(db, role="provider")
    await providers.onboard(user, _onboard())
    with pytest.raises(ConflictError):
        await providers.onboard(user, _onboard())


async def test_verify_provider_logs_audit_action(admin, db):
    provider_user = await factories.make_user(db, role="provider")
    provider = await factories.make_provider(db, provider_user, verified=False)
    admin_user = await factories.make_user(db, role="admin")

    updated, owner = await admin.verify_provider(
        provider.id, ProviderVerifyRequest(is_verified=True), admin_user
    )
    assert updated.is_verified is True
    assert owner.id == provider_user.id

    logs = await admin.audit_logs()
    assert len(logs) == 1
    assert logs[0].action == "VERIFY_PROVIDER"
    assert logs[0].performed_by == admin_user.id


async def test_verify_missing_provider_not_found(admin, db):
    admin_user = await factories.make_user(db, role="admin")
    with pytest.raises(NotFoundError):
        await admin.verify_provider(
            9999, ProviderVerifyRequest(is_verified=True), admin_user
        )


async def test_verify_provider_persists_status(admin, db):
    provider_user = await factories.make_user(db, role="customer")
    provider = await factories.make_provider(db, provider_user, verified=False)
    admin_user = await factories.make_user(db, role="admin")

    provider_id, owner_id = provider.id, provider_user.id

    await admin.verify_provider(
        provider_id, ProviderVerifyRequest(is_verified=True), admin_user
    )

    db.expunge_all()
    stored = await db.get(Provider, provider_id)
    stored_owner = await db.get(User, owner_id)
    assert stored.is_verified is True
    assert stored_owner.role == UserRole.PROVIDER


async def test_reject_provider_persists_status(admin, db):
    provider_user = await factories.make_user(db, role="provider")
    provider = await factories.make_provider(db, provider_user, verified=True)
    admin_user = await factories.make_user(db, role="admin")

    provider_id, owner_id = provider.id, provider_user.id

    await admin.verify_provider(
        provider_id, ProviderVerifyRequest(is_verified=False), admin_user
    )

    db.expunge_all()
    stored = await db.get(Provider, provider_id)
    stored_owner = await db.get(User, owner_id)
    assert stored.is_verified is False
    assert stored_owner.role == UserRole.CUSTOMER


async def test_verify_provider_notifies_owner(admin, db):
    provider_user = await factories.make_user(db, role="customer")
    provider = await factories.make_provider(db, provider_user, verified=False)
    admin_user = await factories.make_user(db, role="admin")

    await admin.verify_provider(
        provider.id, ProviderVerifyRequest(is_verified=True), admin_user
    )

    result = await db.execute(
        select(Notification).where(Notification.user_id == provider_user.id)
    )
    notifications = result.scalars().all()
    assert len(notifications) == 1
    assert notifications[0].notification_type == "provider_verification"


async def test_get_provider_detail_returns_owner(admin, db):
    provider_user = await factories.make_user(db, role="provider")
    provider = await factories.make_provider(db, provider_user)

    found, owner = await admin.get_provider_detail(provider.id)
    assert found.id == provider.id
    assert owner.id == provider_user.id


async def test_get_provider_detail_missing(admin):
    with pytest.raises(NotFoundError):
        await admin.get_provider_detail(9999)


async def test_list_providers_returns_pending_first(admin, db):
    verified_user = await factories.make_user(db, role="provider")
    await factories.make_provider(db, verified_user, verified=True)
    pending_user = await factories.make_user(db, role="customer")
    pending = await factories.make_provider(db, pending_user, verified=False)

    providers = await admin.list_providers()
    assert providers[0].id == pending.id

    pending_only = await admin.list_providers(is_verified=False)
    assert [item.id for item in pending_only] == [pending.id]


async def test_list_users_and_providers(admin, db):
    provider_user = await factories.make_user(db, role="provider")
    await factories.make_provider(db, provider_user, category="Cleaning")
    await factories.make_user(db, role="customer")

    users = await admin.list_users()
    assert len(users) == 2

    providers = await admin.list_providers(category="Cleaning")
    assert len(providers) == 1
    assert providers[0].category == "Cleaning"
