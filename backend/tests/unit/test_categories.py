"""Unit tests for the Category service layer."""
import pytest

from app.common.pagination import PageParams
from app.core.exceptions import ConflictError, NotFoundError
from app.schemas.category import CategoryCreate, CategoryUpdate
from app.services.category_service import CategoryService
from tests import factories


@pytest.fixture
async def service(db):
    return CategoryService(db)


async def test_create_generates_slug(service, db):
    category = await service.create(CategoryCreate(name="House Cleaning"))
    assert category.id is not None
    assert category.slug == "house-cleaning"


async def test_create_duplicate_name_conflict(service, db):
    await service.create(CategoryCreate(name="Cleaning"))
    with pytest.raises(ConflictError):
        await service.create(CategoryCreate(name="Cleaning"))


async def test_create_duplicate_slug_conflict(service, db):
    await service.create(CategoryCreate(name="Cleaning", slug="clean"))
    with pytest.raises(ConflictError):
        await service.create(CategoryCreate(name="Deep Clean", slug="clean"))


async def test_get_missing_raises_not_found(service, db):
    with pytest.raises(NotFoundError):
        await service.get(9999)


async def test_update_category(service, db):
    category = await service.create(CategoryCreate(name="Cleaning"))
    updated = await service.update(category.id, CategoryUpdate(name="Deep Cleaning"))
    assert updated.name == "Deep Cleaning"
    assert updated.slug == "deep-cleaning"


async def test_delete_category(service, db):
    category = await service.create(CategoryCreate(name="Temp"))
    await service.delete(category.id)
    with pytest.raises(NotFoundError):
        await service.get(category.id)


async def test_list_pagination(service, db):
    for name in ["A", "B", "C"]:
        await service.create(CategoryCreate(name=name))
    page = await service.list(PageParams(page=1, page_size=2))
    assert page.total == 3
    assert len(page.items) == 2
    assert page.pages == 2


async def test_delete_category_with_active_services_conflict(service, db):
    category = await factories.make_category(db, name="Cleaning")
    provider_user = await factories.make_user(db, role="provider")
    provider = await factories.make_provider(db, provider_user)
    await factories.make_service(db, provider=provider, category=category)

    with pytest.raises(ConflictError):
        await service.delete(category.id)
