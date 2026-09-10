from uuid import UUID

from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    query: str = Field(min_length=2, max_length=500)
    limit: int | None = Field(default=None, ge=1)


class SearchResultResponse(BaseModel):
    chunk_id: UUID
    page_number: int
    chunk_index: int
    content: str
    text: str
    score: float
    source_url: str


class SearchResponse(BaseModel):
    query: str
    result_count: int
    results: list[SearchResultResponse]
