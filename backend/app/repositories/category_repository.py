"""Data-access layer for categories."""
from typing import Optional, Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.pagination import PageParams
from app.models.category import Category
from app.repositories.base import BaseRepository
from app.schemas.category import CategoryCreate, CategoryUpdate


class CategoryRepository(BaseRepository):
    """Queries for :class:`~app.models.category.Category`."""

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db)

    async def get(self, category_id: int) -> Optional[Category]:
        """Return a category by primary key, or ``None`` if absent."""
        result = await self.db.execute(
            select(Category).where(Category.id == category_id)
        )
        return result.scalar_one_or_none()

    async def get_by_slug(self, slug: str) -> Optional[Category]:
        """Return a category by its unique slug, or ``None``."""
        result = await self.db.execute(
            select(Category).where(Category.slug == slug)
        )
        return result.scalar_one_or_none()

    async def get_by_name(self, name: str) -> Optional[Category]:
        """Return a category by name (case-insensitive), or ``None``."""
        result = await self.db.execute(
            select(Category).where(func.lower(Category.name) == name.lower())
        )
        return result.scalar_one_or_none()

    async def list(
        self,
        params: PageParams,
        include_inactive: bool = False,
    ) -> tuple[Sequence[Category], int]:
        """Return a page of categories and the total matching count.

        Inactive categories are hidden unless ``include_inactive`` is set
        (an admin-only capability).
        """
        conditions = []
        if not include_inactive:
            conditions.append(Category.is_active.is_(True))

        count_stmt = select(func.count(Category.id))
        list_stmt = select(Category).order_by(Category.name)
        if conditions:
            count_stmt = count_stmt.where(*conditions)
            list_stmt = list_stmt.where(*conditions)

        total = (await self.db.execute(count_stmt)).scalar_one()
        items = (
            (await self.db.execute(list_stmt.offset(params.offset).limit(params.page_size)))
            .scalars()
            .all()
        )
        return items, total

    async def create(self, data: CategoryCreate, slug: str) -> Category:
        """Persist a new category (``slug`` resolved by the service layer)."""
        category = Category(
            name=data.name,
            slug=slug,
            description=data.description or "",
            icon=data.icon or "",
            is_active=data.is_active,
        )
        self.db.add(category)
        await self.db.flush()
        return category

    async def update(self, category: Category, data: CategoryUpdate) -> Category:
        """Apply the set fields of ``data`` onto ``category`` in place."""
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(category, field, value)
        await self.db.flush()
        return category

    async def delete(self, category: Category) -> None:
        """Remove a category from the database."""
        await self.db.delete(category)
        await self.db.flush()
