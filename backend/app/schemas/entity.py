from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class EntityResponse(BaseModel):
    id: UUID
    document_id: UUID
    page_id: UUID
    page_number: int
    entity_type: str
    entity_value: str
    confidence: float | None
    source: str
    bounding_box: list[list[float]] | None
    created_at: datetime
