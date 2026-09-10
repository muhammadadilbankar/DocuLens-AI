from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class PageResponse(BaseModel):
    id: UUID
    page_number: int
    image_width: int
    image_height: int
    image_url: str
    preprocessed_image_url: str | None
    ocr_completed: bool
    average_ocr_confidence: float | None
    created_at: datetime


class OcrBlockResponse(BaseModel):
    id: UUID
    text: str
    confidence: float
    bounding_box: list[list[float]]
    reading_order: int


class PageDetailResponse(PageResponse):
    document_id: UUID
    raw_text: str | None
    cleaned_text: str | None
    ocr_blocks: list[OcrBlockResponse]
