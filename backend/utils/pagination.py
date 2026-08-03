from typing import TypeVar, Generic, Sequence
from pydantic import BaseModel
from sqlalchemy.orm import Query

T = TypeVar("T")

class Page(BaseModel, Generic[T]):
    items: Sequence[T]
    total: int
    page: int
    size: int

def paginate(query: Query, page: int = 1, size: int = 20) -> dict:
    total = query.count()
    items = query.offset((page - 1) * size).limit(size).all()
    return {
        "items": items,
        "total": total,
        "page": page,
        "size": size
    }
