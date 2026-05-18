from pydantic import BaseModel, Field


class PaginatedResponse[T](BaseModel):
    items: list[T] = Field(
        ...,
        description="List of results for the current page.",
    )
    total: int = Field(
        ...,
        description="Total number of records matching the query across all pages.",
        examples=[150],
    )
    page: int = Field(
        ...,
        description="Current page number (1-based).",
        examples=[1],
    )
    size: int = Field(
        ...,
        description="Number of results per page.",
        examples=[20],
    )
    pages: int = Field(
        ...,
        description="Total number of pages given the current `size`.",
        examples=[8],
    )

    @classmethod
    def create(cls, items: list, total: int, page: int, size: int) -> "PaginatedResponse":
        pages = (total + size - 1) // size  # ceil division
        return cls(items=items, total=total, page=page, size=size, pages=pages)
