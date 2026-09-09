from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class PageResponse(BaseModel):
    id: UUID
    page_number: int
    image_width: int
    image_height: int
    image_url: str
    created_at: datetime
