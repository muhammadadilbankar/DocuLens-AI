import struct
from pathlib import Path
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse, Response
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.database import get_db
from app.models.document import Document, DocumentStatus
from app.models.entity import Entity
from app.models.page import Page
from app.schemas.document import DocumentResponse, DocumentUploadResponse
from app.schemas.entity import EntityResponse
from app.schemas.page import OcrBlockResponse, PageDetailResponse, PageResponse
from app.schemas.search import SearchRequest, SearchResponse, SearchResultResponse
from app.services.document_service import (
    DocumentPersistenceError,
    UploadValidationError,
    store_uploaded_document,
)
from app.services.entity_service import process_document_entities
from app.services.export_service import ExportFormat, build_document_export
from app.services.page_service import convert_document_pages, get_document_pages
from app.services.preprocessing_service import preprocess_document_pages
from app.services.ocr_service import process_document_ocr
from app.services.search_service import SearchIndexError, process_document_index, search_document

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
        entity_count=len(document.entities),
        indexed_chunk_count=len(document.chunks),
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
    database: Annotated[Session, Depends(get_db, scope="function")],
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
    database: Annotated[Session, Depends(get_db, scope="function")],
) -> DocumentResponse:
    return _document_response(_get_document_or_404(database, document_id))


@router.post(
    "/{document_id}/process",
    response_model=DocumentResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Start or resume document processing",
)
def process_document(
    document_id: UUID,
    background_tasks: BackgroundTasks,
    database: Annotated[Session, Depends(get_db, scope="function")],
    settings: Annotated[Settings, Depends(get_settings)],
) -> DocumentResponse:
    document = _get_document_or_404(database, document_id)
    if document.status == DocumentStatus.CONVERTING:
        raise HTTPException(status_code=409, detail="Document conversion is already running.")
    if document.status == DocumentStatus.EXTRACTING_ENTITIES:
        background_tasks.add_task(process_document_entities, document.id, settings)
        return _document_response(document)
    if document.status == DocumentStatus.INDEXING:
        background_tasks.add_task(process_document_index, document.id, settings)
        return _document_response(document)
    if document.status == DocumentStatus.COMPLETED:
        if document.chunks:
            raise HTTPException(status_code=409, detail="Document processing is already complete.")
        document.status = DocumentStatus.INDEXING
        document.error_message = None
        database.commit()
        database.refresh(document)
        background_tasks.add_task(process_document_index, document.id, settings)
        return _document_response(document)

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
    database: Annotated[Session, Depends(get_db, scope="function")],
) -> list[PageResponse]:
    _get_document_or_404(database, document_id)
    return [
        _page_response(page, document_id)
        for page in get_document_pages(database, document_id)
    ]


def _entity_response(entity: Entity) -> EntityResponse:
    return EntityResponse(
        id=entity.id,
        document_id=entity.document_id,
        page_id=entity.page_id,
        page_number=entity.page.page_number,
        entity_type=entity.entity_type,
        entity_value=entity.entity_value,
        confidence=entity.confidence,
        source=entity.source,
        bounding_box=entity.bounding_box,
        created_at=entity.created_at,
    )


@router.get(
    "/{document_id}/entities",
    response_model=list[EntityResponse],
    summary="List extracted document entities",
)
def list_document_entities(
    document_id: UUID,
    database: Annotated[Session, Depends(get_db, scope="function")],
    page_number: int | None = None,
) -> list[EntityResponse]:
    _get_document_or_404(database, document_id)
    query = database.query(Entity).filter(Entity.document_id == document_id)
    if page_number is not None:
        query = query.join(Page).filter(Page.page_number == page_number)
    entities = query.order_by(Entity.created_at, Entity.id).all()
    return [_entity_response(entity) for entity in entities]


@router.post(
    "/{document_id}/search",
    response_model=SearchResponse,
    summary="Search indexed document text",
)
def search_document_text(
    document_id: UUID,
    request: SearchRequest,
    database: Annotated[Session, Depends(get_db, scope="function")],
    settings: Annotated[Settings, Depends(get_settings)],
) -> SearchResponse:
    document = _get_document_or_404(database, document_id)
    limit = request.limit or settings.search_default_limit
    if limit > settings.search_max_limit:
        raise HTTPException(
            status_code=422,
            detail=f"Search limit cannot exceed {settings.search_max_limit}.",
        )
    try:
        matches = search_document(database, document, request.query, limit, settings)
    except SearchIndexError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    results = [
        SearchResultResponse(
            chunk_id=match.chunk_id,
            page_number=match.page_number,
            chunk_index=match.chunk_index,
            content=match.content,
            text=match.content,
            score=match.score,
            source_url=f"/documents/{document_id}/pages/{match.page_number}",
        )
        for match in matches
    ]
    return SearchResponse(
        query=" ".join(request.query.split()),
        result_count=len(results),
        results=results,
    )


@router.get(
    "/{document_id}/export",
    response_class=Response,
    summary="Export document metadata and extracted information",
)
def export_document(
    document_id: UUID,
    database: Annotated[Session, Depends(get_db, scope="function")],
    export_format: Annotated[ExportFormat, Query(alias="format")] = "json",
) -> Response:
    document = _get_document_or_404(database, document_id)
    if document.status != DocumentStatus.COMPLETED:
        raise HTTPException(
            status_code=409,
            detail="Document exports are available after processing completes.",
        )

    artifact = build_document_export(document, export_format)
    return Response(
        content=artifact.content,
        media_type=artifact.media_type,
        headers={"Content-Disposition": f'attachment; filename="{artifact.filename}"'},
    )


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
    database: Annotated[Session, Depends(get_db, scope="function")],
) -> PageDetailResponse:
    page = database.query(Page).filter_by(
        document_id=document_id, page_number=page_number
    ).one_or_none()
    if page is None:
        raise HTTPException(status_code=404, detail="Document page not found.")

    summary = _page_response(page, document_id)
    coordinate_width, coordinate_height = _png_dimensions(
        Path(page.preprocessed_image_path or page.original_image_path),
        fallback=(page.image_width, page.image_height),
    )
    return PageDetailResponse(
        **summary.model_dump(),
        document_id=document_id,
        ocr_coordinate_width=coordinate_width,
        ocr_coordinate_height=coordinate_height,
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
        entities=[_entity_response(entity) for entity in page.entities],
    )


def _png_dimensions(image_path: Path, fallback: tuple[int, int]) -> tuple[int, int]:
    try:
        with image_path.open("rb") as image_file:
            header = image_file.read(24)
        if len(header) == 24 and header[:8] == b"\x89PNG\r\n\x1a\n":
            return struct.unpack(">II", header[16:24])
    except OSError:
        pass
    return fallback


@router.get(
    "/{document_id}/pages/{page_number}/image",
    response_class=FileResponse,
    summary="Get an original rendered page image",
)
def get_page_image(
    document_id: UUID,
    page_number: int,
    database: Annotated[Session, Depends(get_db, scope="function")],
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
