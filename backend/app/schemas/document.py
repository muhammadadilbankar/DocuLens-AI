from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.models.document import DocumentStatus


class DocumentUploadResponse(BaseModel):
    document_id: UUID
    filename: str
    status: DocumentStatus
    created_at: datetime


class DocumentResponse(BaseModel):
    id: UUID
    original_filename: str
    page_count: int
    ocr_page_count: int
    entity_count: int
    status: DocumentStatus
    created_at: datetime
    processed_at: datetime | None
    error_message: str | None
