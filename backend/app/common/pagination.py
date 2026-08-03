"""Pagination helpers.

Provides a query-parameter model plus a generic response wrapper. Controllers
paginate repository results and return :class:`PaginatedResponse`; FastAPI
serialises the generic ``items`` field to the concrete element schema.
"""
from typing import Generic, List, Optional, TypeVar

from pydantic import BaseModel, Field

from app.core.config import settings

T = TypeVar("T")


class PageParams(BaseModel):
    """Common pagination query parameters."""

    page: int = Field(default=1, ge=1, description="1-based page number.")
    page_size: int = Field(
        default=settings.DEFAULT_PAGE_SIZE,
        ge=1,
        le=settings.MAX_PAGE_SIZE,
        description="Number of items per page.",
    )

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size


class Page(BaseModel, Generic[T]):
    """Standardised, page-shaped response."""

    items: List[T]
    total: int
    page: int
    page_size: int
    pages: int

    @classmethod
    def create(
        cls,
        items: List[T],
        total: int,
        page: int,
        page_size: int,
    ) -> "Page[T]":
        pages = (total + page_size - 1) // page_size if page_size > 0 else 0
        return cls(items=items, total=total, page=page, page_size=page_size, pages=pages)


def paginate_params(params: Optional[PageParams] = None) -> PageParams:
    """Normalise missing pagination params to defaults."""
    return params or PageParams()
