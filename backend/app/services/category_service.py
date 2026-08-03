"""Business logic for categories.

All rules (slug generation, uniqueness, delete-protection) live here so they can
be unit-tested independently of HTTP. Controllers stay thin and delegate to
:class:`CategoryService`.
"""
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.pagination import Page, PageParams
from app.common.utils import slugify
from app.core.exceptions import ConflictError, NotFoundError
from app.models.category import Category
from app.models.service import Service
from app.repositories.category_repository import CategoryRepository
from app.schemas.category import CategoryCreate, CategoryRead, CategoryUpdate


class CategoryService:
    """Encapsulates category operations and their invariants."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = CategoryRepository(db)

    async def get(self, category_id: int) -> Category:
        """Return a category, raising ``NotFoundError`` if it is missing."""
        category = await self.repo.get(category_id)
        if category is None:
            raise NotFoundError("Category not found.")
        return category

    async def list(
        self, params: PageParams, include_inactive: bool = False
    ) -> Page[CategoryRead]:
        """Return a page of categories (optionally including inactive ones)."""
        items, total = await self.repo.list(params, include_inactive=include_inactive)
        return Page.create(list(items), total, params.page, params.page_size)

    async def create(self, data: CategoryCreate) -> Category:
        """Create a category, enforcing unique name and slug."""
        slug = data.slug or slugify(data.name)

        if await self.repo.get_by_slug(slug):
            raise ConflictError("A category with this slug already exists.")
        if await self.repo.get_by_name(data.name):
            raise ConflictError("A category with this name already exists.")

        category = await self.repo.create(data, slug)
        await self.db.commit()
        await self.db.refresh(category)
        return category

    async def update(self, category_id: int, data: CategoryUpdate) -> Category:
        """Update a category, re-checking uniqueness for any changed fields."""
        category = await self.get(category_id)
        payload = data.model_dump(exclude_unset=True)

        # A new slug is the explicit one, else re-derive it from a changed name.
        new_slug = payload.get("slug") or (
            slugify(payload["name"]) if payload.get("name") else None
        )
        if new_slug and new_slug != category.slug and await self.repo.get_by_slug(new_slug):
            raise ConflictError("A category with this slug already exists.")
        if payload.get("name"):
            existing = await self.repo.get_by_name(payload["name"])
            if existing is not None and existing.id != category.id:
                raise ConflictError("A category with this name already exists.")

        if new_slug:
            payload["slug"] = new_slug

        updated = await self.repo.update(category, CategoryUpdate(**payload))
        await self.db.commit()
        await self.db.refresh(updated)
        return updated

    async def delete(self, category_id: int) -> None:
        """Delete a category, blocking the action if it has active services."""
        category = await self.get(category_id)

        active_count = (
            await self.db.execute(
                select(func.count(Service.id)).where(
                    Service.category_id == category_id,
                    Service.is_active.is_(True),
                )
            )
        ).scalar_one()
        if active_count:
            raise ConflictError(
                "Cannot delete a category that still has active services."
            )

        await self.repo.delete(category)
        await self.db.commit()
