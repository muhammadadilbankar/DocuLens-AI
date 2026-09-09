import logging
import uuid
from pathlib import Path

from sqlalchemy import select

from app.core.config import Settings
from app.core.database import SessionLocal
from app.models.document import Document, DocumentStatus
from app.models.page import Page
from app.services.pdf_service import RenderedPage, render_pdf_pages

logger = logging.getLogger(__name__)


def convert_document_pages(document_id: uuid.UUID, settings: Settings) -> None:
    rendered_pages: list[RenderedPage] = []
    with SessionLocal() as database:
        document = database.get(Document, document_id)
        if document is None:
            logger.error("Document %s disappeared before conversion", document_id)
            return

        output_directory = (
            settings.resolved_processed_directory / str(document_id) / "original"
        )

        try:
            rendered_pages = render_pdf_pages(
                Path(document.file_path),
                output_directory,
                settings.pdf_render_dpi,
            )
            database.add_all(
                [
                    Page(
                        document_id=document.id,
                        page_number=rendered.page_number,
                        original_image_path=str(rendered.image_path),
                        image_width=rendered.width,
                        image_height=rendered.height,
                    )
                    for rendered in rendered_pages
                ]
            )
            document.page_count = len(rendered_pages)
            document.status = DocumentStatus.PREPROCESSING
            document.error_message = None
            database.commit()
        except Exception as exc:
            database.rollback()
            _remove_page_files(rendered_pages)
            failed_document = database.get(Document, document_id)
            if failed_document is not None:
                failed_document.status = DocumentStatus.FAILED
                failed_document.error_message = str(exc)[:2000]
                database.commit()
            logger.exception("Page conversion failed for document %s", document_id)


def get_document_pages(database, document_id: uuid.UUID) -> list[Page]:
    statement = (
        select(Page)
        .where(Page.document_id == document_id)
        .order_by(Page.page_number)
    )
    return list(database.scalars(statement).all())


def _remove_page_files(rendered_pages: list[RenderedPage]) -> None:
    parent_directories: set[Path] = set()
    for rendered_page in rendered_pages:
        parent_directories.add(rendered_page.image_path.parent)
        rendered_page.image_path.unlink(missing_ok=True)
    for directory in sorted(parent_directories, key=lambda path: len(path.parts), reverse=True):
        try:
            directory.rmdir()
            directory.parent.rmdir()
        except OSError:
            pass
