"""Unit tests for the admin + provider-onboarding services."""
import pytest

from app.core.exceptions import ConflictError, NotFoundError
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

    updated = await admin.verify_provider(
        provider.id, ProviderVerifyRequest(is_verified=True), admin_user
    )
    assert updated.is_verified is True

    logs = await admin.audit_logs()
    assert len(logs) == 1
    assert logs[0].action == "VERIFY_PROVIDER"
    assert logs[0].performed_by == admin_user.id


async def test_reject_pending_provider_returns_none(admin, db):
    customer = await factories.make_user(db, role="customer")
    provider = await factories.make_provider(db, customer, verified=False)
    admin_user = await factories.make_user(db, role="admin")

    result = await admin.verify_provider(
        provider.id,
        ProviderVerifyRequest(is_verified=False),
        admin_user,
    )

    assert result is None


async def test_verify_missing_provider_not_found(admin, db):
    admin_user = await factories.make_user(db, role="admin")
    with pytest.raises(NotFoundError):
        await admin.verify_provider(
            9999, ProviderVerifyRequest(is_verified=True), admin_user
        )


async def test_list_users_and_providers(admin, db):
    provider_user = await factories.make_user(db, role="provider")
    await factories.make_provider(db, provider_user, category="Cleaning")
    await factories.make_user(db, role="customer")

    users = await admin.list_users()
    assert len(users) == 2

    providers = await admin.list_providers(category="Cleaning")
    assert len(providers) == 1
    assert providers[0].category == "Cleaning"


async def test_get_provider_details(admin, db):
    provider_user = await factories.make_user(db, role="provider", full_name="Master Plumber")
    provider = await factories.make_provider(db, provider_user, business_name="Plumbing Pros")

    details = await admin.get_provider_details(provider.id)
    assert details["id"] == provider.id
    assert details["business_name"] == "Plumbing Pros"
    assert details["owner"].full_name == "Master Plumber"
    assert details["service_count"] == 0
    assert details["booking_count"] == 0



async def test_verify_provider_updates_owner_verification(admin, db):
    customer = await factories.make_user(db, role="customer")
    provider = await factories.make_provider(db, customer, verified=False)
    admin_user = await factories.make_user(db, role="admin")

    updated = await admin.verify_provider(
        provider.id, ProviderVerifyRequest(is_verified=True), admin_user
    )
    assert updated.is_verified is True

    # Check owner role and is_verified updated
    owner = await admin.users.get(customer.id)
    assert owner.role.value == "provider"
    assert owner.is_verified is True

