from pathlib import Path
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.database import get_db
from app.models.document import Document, DocumentStatus
from app.models.page import Page
from app.schemas.document import DocumentResponse, DocumentUploadResponse
from app.schemas.page import OcrBlockResponse, PageDetailResponse, PageResponse
from app.services.document_service import (
    DocumentPersistenceError,
    UploadValidationError,
    store_uploaded_document,
)
from app.services.page_service import convert_document_pages, get_document_pages
from app.services.preprocessing_service import preprocess_document_pages
from app.services.ocr_service import process_document_ocr

router = APIRouter(prefix="/documents")


def _get_document_or_404(database: Session, document_id: UUID) -> Document:
    document = database.get(Document, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found.")
    return document


def _document_response(document: Document) -> DocumentResponse:
    return DocumentResponse(
        id=document.id,
        original_filename=document.original_filename,
        page_count=document.page_count,
        ocr_page_count=sum(page.raw_text is not None for page in document.pages),
        status=document.status,
        created_at=document.created_at,
        processed_at=document.processed_at,
        error_message=document.error_message,
    )


@router.post(
    "/upload",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a scanned PDF",
)
async def upload_document(
    file: Annotated[UploadFile, File(description="Scanned PDF document")],
    database: Annotated[Session, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> DocumentUploadResponse:
    try:
        document = await store_uploaded_document(file, database, settings)
    except UploadValidationError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc
    except DocumentPersistenceError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
        ) from exc

    return DocumentUploadResponse(
        document_id=document.id,
        filename=document.original_filename,
        status=document.status,
        created_at=document.created_at,
    )


@router.get(
    "/{document_id}",
    response_model=DocumentResponse,
    summary="Get document metadata",
)
def get_document(
    document_id: UUID,
    database: Annotated[Session, Depends(get_db)],
) -> DocumentResponse:
    return _document_response(_get_document_or_404(database, document_id))


@router.post(
    "/{document_id}/process",
    response_model=DocumentResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Start PDF page conversion",
)
def process_document(
    document_id: UUID,
    background_tasks: BackgroundTasks,
    database: Annotated[Session, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> DocumentResponse:
    document = _get_document_or_404(database, document_id)
    if document.status == DocumentStatus.CONVERTING:
        raise HTTPException(status_code=409, detail="Document conversion is already running.")
    if document.status in {
        DocumentStatus.EXTRACTING_ENTITIES,
        DocumentStatus.INDEXING,
        DocumentStatus.COMPLETED,
    }:
        raise HTTPException(status_code=409, detail="Document OCR is already complete.")

    pages = get_document_pages(database, document_id) if document.page_count > 0 else []
    if pages and all(page.preprocessed_image_path for page in pages) and document.status in {
        DocumentStatus.OCR_PROCESSING,
        DocumentStatus.FAILED,
    }:
        document.status = DocumentStatus.OCR_PROCESSING
        document.error_message = None
        database.commit()
        database.refresh(document)
        background_tasks.add_task(process_document_ocr, document.id, settings)
        return _document_response(document)

    if document.page_count > 0:
        if document.status not in {DocumentStatus.PREPROCESSING, DocumentStatus.FAILED}:
            raise HTTPException(
                status_code=409,
                detail=f"Document cannot be preprocessed while status is {document.status.value}.",
            )
        document.status = DocumentStatus.PREPROCESSING
        document.error_message = None
        database.commit()
        database.refresh(document)
        background_tasks.add_task(preprocess_document_pages, document.id, settings)
        return _document_response(document)

    if document.status not in {DocumentStatus.UPLOADED, DocumentStatus.FAILED}:
        raise HTTPException(
            status_code=409,
            detail=f"Document cannot be converted while status is {document.status.value}.",
        )

    document.status = DocumentStatus.CONVERTING
    document.error_message = None
    database.commit()
    database.refresh(document)
    background_tasks.add_task(convert_document_pages, document.id, settings)
    return _document_response(document)


@router.get(
    "/{document_id}/pages",
    response_model=list[PageResponse],
    summary="List converted document pages",
)
def list_document_pages(
    document_id: UUID,
    database: Annotated[Session, Depends(get_db)],
) -> list[PageResponse]:
    _get_document_or_404(database, document_id)
    return [
        _page_response(page, document_id)
        for page in get_document_pages(database, document_id)
    ]


def _page_response(page: Page, document_id: UUID) -> PageResponse:
    return PageResponse(
        id=page.id,
        page_number=page.page_number,
        image_width=page.image_width,
        image_height=page.image_height,
        image_url=f"/documents/{document_id}/pages/{page.page_number}/image",
        preprocessed_image_url=(
            f"/documents/{document_id}/pages/{page.page_number}/image?variant=preprocessed"
            if page.preprocessed_image_path
            else None
        ),
        ocr_completed=page.raw_text is not None,
        average_ocr_confidence=page.average_ocr_confidence,
        created_at=page.created_at,
    )


@router.get(
    "/{document_id}/pages/{page_number}",
    response_model=PageDetailResponse,
    summary="Get page OCR details",
)
def get_document_page(
    document_id: UUID,
    page_number: int,
    database: Annotated[Session, Depends(get_db)],
) -> PageDetailResponse:
    page = database.query(Page).filter_by(
        document_id=document_id, page_number=page_number
    ).one_or_none()
    if page is None:
        raise HTTPException(status_code=404, detail="Document page not found.")

    summary = _page_response(page, document_id)
    return PageDetailResponse(
        **summary.model_dump(),
        document_id=document_id,
        raw_text=page.raw_text,
        cleaned_text=page.cleaned_text,
        ocr_blocks=[
            OcrBlockResponse(
                id=block.id,
                text=block.text,
                confidence=block.confidence,
                bounding_box=block.bounding_box,
                reading_order=block.reading_order,
            )
            for block in page.ocr_blocks
        ],
    )


@router.get(
    "/{document_id}/pages/{page_number}/image",
    response_class=FileResponse,
    summary="Get an original rendered page image",
)
def get_page_image(
    document_id: UUID,
    page_number: int,
    database: Annotated[Session, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
    variant: Literal["original", "preprocessed"] = "original",
) -> FileResponse:
    page = database.query(Page).filter_by(
        document_id=document_id, page_number=page_number
    ).one_or_none()
    if page is None:
        raise HTTPException(status_code=404, detail="Document page not found.")

    selected_path = (
        page.preprocessed_image_path
        if variant == "preprocessed"
        else page.original_image_path
    )
    if not selected_path:
        raise HTTPException(status_code=404, detail="Preprocessed page image not found.")
    image_path = Path(selected_path).resolve()
    processed_root = settings.resolved_processed_directory.resolve()
    if not image_path.is_relative_to(processed_root) or not image_path.is_file():
        raise HTTPException(status_code=404, detail="Document page image not found.")
    return FileResponse(image_path, media_type="image/png", filename=image_path.name)
