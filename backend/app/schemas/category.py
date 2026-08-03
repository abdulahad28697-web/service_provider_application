"""Category Pydantic schemas (request/response models)."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.common.pagination import Page


class CategoryBase(BaseModel):
    """Shared fields for create/read of a category."""

    name: str = Field(..., min_length=1, max_length=120)
    slug: Optional[str] = Field(default=None, max_length=140)
    description: Optional[str] = Field(default="", max_length=2000)
    icon: Optional[str] = Field(default="", max_length=255)
    is_active: bool = True


class CategoryCreate(CategoryBase):
    """Payload for creating a category."""


class CategoryUpdate(BaseModel):
    """Payload for updating a category; all fields optional."""

    name: Optional[str] = Field(default=None, min_length=1, max_length=120)
    slug: Optional[str] = Field(default=None, max_length=140)
    description: Optional[str] = Field(default=None, max_length=2000)
    icon: Optional[str] = Field(default=None, max_length=255)
    is_active: Optional[bool] = None


class CategoryRead(CategoryBase):
    """A category as returned to API consumers."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime


CategoryPage = Page[CategoryRead]
