"""Filter model and builder for the services list/search endpoints.

:class:`ServiceFilters` captures every optional query criterion. The builder
turns them into SQLAlchemy conditions in one place so the repository and any
future callers share identical semantics. This module lives in the repository
layer because it constructs SQL statements.
"""
from dataclasses import dataclass, field
from typing import Optional

from sqlalchemy import Select, and_, or_
from sqlalchemy.sql.expression import select

from app.models.service import Service


@dataclass
class ServiceFilters:
    """Immutable-ish container of service query filters."""

    category_id: Optional[int] = None
    provider_id: Optional[int] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    is_active: Optional[bool] = True
    is_featured: Optional[bool] = None
    query: Optional[str] = None
    sort_by: str = "newest"
    sort_dir: str = "desc"
    # Whitelisted columns we are allowed to sort on.
    sortable_fields: set[str] = field(
        default_factory=lambda: {"newest", "oldest", "price_asc", "price_desc", "title"}
    )


def _clauses(f: ServiceFilters) -> list:
    """Build the WHERE conditions implied by a :class:`ServiceFilters`."""
    conds = []
    if f.category_id is not None:
        conds.append(Service.category_id == f.category_id)
    if f.provider_id is not None:
        conds.append(Service.provider_id == f.provider_id)
    if f.min_price is not None:
        conds.append(Service.price >= f.min_price)
    if f.max_price is not None:
        conds.append(Service.price <= f.max_price)
    if f.is_active is not None:
        conds.append(Service.is_active.is_(f.is_active))
    if f.is_featured is not None:
        conds.append(Service.is_featured.is_(f.is_featured))
    if f.query:
        pattern = f"%{f.query.strip()}%"
        conds.append(
            or_(Service.title.ilike(pattern), Service.description.ilike(pattern))
        )
    return conds


def apply_filters(statement: Select, f: ServiceFilters) -> Select:
    """Apply the clauses of ``f`` to a select statement."""
    clauses = _clauses(f)
    return statement.where(and_(*clauses)) if clauses else statement


def order_by_clause(f: ServiceFilters) -> object:
    """Resolve the requested sort into a SQLAlchemy sort expression.

    Unknown or invalid sort keys fall back to "newest" so user input can never
    inject an arbitrary column into the ORDER BY.
    """
    sort_key = f.sort_by if f.sort_by in f.sortable_fields else "newest"
    if sort_key == "price_asc":
        return Service.price.asc()
    if sort_key == "price_desc":
        return Service.price.desc()
    if sort_key == "title":
        return Service.title.asc()
    if sort_key == "oldest":
        return Service.created_at.asc()
    # "newest" is the default.
    return Service.created_at.desc()


def base_select(f: ServiceFilters = ServiceFilters()) -> Select:
    """Return a filtered, ordered select statement over services."""
    stmt = apply_filters(select(Service), f)
    return stmt.order_by(order_by_clause(f))
