from pydantic import BaseModel
from typing import Generic, TypeVar

T = TypeVar("T")

class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    size: int
    pages: int

    @classmethod
    def create(cls, items: list, total: int, page: int, size: int) -> "PaginatedResponse":
        pages = (total + size - 1) // size  # ceil division
        return cls(items=items, total=total, page=page, size=size, pages=pages)