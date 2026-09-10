import shutil
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from uuid import UUID, uuid4

from fastapi import UploadFile
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models.document import Document, DocumentStatus

PDF_CONTENT_TYPES = {"application/pdf", "application/x-pdf"}
PDF_SIGNATURE = b"%PDF-"
READ_CHUNK_SIZE = 1024 * 1024


class UploadValidationError(ValueError):
    def __init__(self, message: str, status_code: int = 400) -> None:
        super().__init__(message)
        self.status_code = status_code


class DocumentPersistenceError(RuntimeError):
    pass


class DocumentDeletionError(RuntimeError):
    pass


@dataclass(frozen=True)
class DocumentDeletionResult:
    document_id: UUID
    removed_artifacts: list[str]
    cleanup_warnings: list[str]


def _safe_original_filename(filename: str | None) -> str:
    if not filename:
        raise UploadValidationError("A PDF filename is required.")

    normalized = filename.replace("\\", "/")
    safe_name = PurePosixPath(normalized).name.strip()
    if not safe_name or Path(safe_name).suffix.lower() != ".pdf":
        raise UploadValidationError("Only files with a .pdf extension are accepted.", 415)
    return safe_name[:255]


async def store_uploaded_document(
    upload: UploadFile,
    database: Session,
    settings: Settings,
) -> Document:
    original_filename = _safe_original_filename(upload.filename)
    if upload.content_type not in PDF_CONTENT_TYPES:
        raise UploadValidationError(
            "The uploaded file must have the application/pdf content type.", 415
        )

    upload_directory = settings.resolved_upload_directory
    upload_directory.mkdir(parents=True, exist_ok=True)
    stored_filename = f"{uuid4()}.pdf"
    destination = upload_directory / stored_filename
    total_bytes = 0

    try:
        with destination.open("wb") as output:
            chunk = await upload.read(READ_CHUNK_SIZE)
            if not chunk.startswith(PDF_SIGNATURE):
                raise UploadValidationError(
                    "The file content is not a valid PDF document.", 415
                )

            while chunk:
                total_bytes += len(chunk)
                if total_bytes > settings.max_upload_size_bytes:
                    raise UploadValidationError(
                        f"PDF exceeds the {settings.max_upload_size_mb} MB upload limit.",
                        413,
                    )
                output.write(chunk)
                chunk = await upload.read(READ_CHUNK_SIZE)

        document = Document(
            original_filename=original_filename,
            stored_filename=stored_filename,
            file_path=str(destination.resolve()),
            status=DocumentStatus.UPLOADED,
        )
        database.add(document)
        database.commit()
        database.refresh(document)
        return document
    except UploadValidationError:
        destination.unlink(missing_ok=True)
        raise
    except (OSError, SQLAlchemyError) as exc:
        database.rollback()
        destination.unlink(missing_ok=True)
        raise DocumentPersistenceError(
            "The document could not be stored. Check the server and database configuration."
        ) from exc
    finally:
        await upload.close()


def delete_stored_document(
    document: Document,
    database: Session,
    settings: Settings,
) -> DocumentDeletionResult:
    document_id = document.id
    uploaded_pdf = Path(document.file_path)
    processed_directory = settings.resolved_processed_directory / str(document_id)
    search_index = settings.resolved_search_index_directory / f"{document_id}.faiss"

    try:
        database.delete(document)
        database.commit()
    except SQLAlchemyError as exc:
        database.rollback()
        raise DocumentDeletionError(
            "The document database record could not be deleted. No files were removed."
        ) from exc

    removed_artifacts: list[str] = []
    cleanup_warnings: list[str] = []
    _remove_file_within_root(
        uploaded_pdf,
        settings.resolved_upload_directory,
        "uploaded PDF",
        removed_artifacts,
        cleanup_warnings,
    )
    _remove_directory_within_root(
        processed_directory,
        settings.resolved_processed_directory,
        "processed page images",
        removed_artifacts,
        cleanup_warnings,
    )
    _remove_file_within_root(
        search_index,
        settings.resolved_search_index_directory,
        "FAISS search index",
        removed_artifacts,
        cleanup_warnings,
    )
    search_root = settings.resolved_search_index_directory.resolve()
    if search_root.is_dir():
        for temporary_index in search_root.glob(f".{document_id}.*.tmp"):
            _remove_file_within_root(
                temporary_index,
                search_root,
                "temporary FAISS index",
                removed_artifacts,
                cleanup_warnings,
            )
    return DocumentDeletionResult(document_id, removed_artifacts, cleanup_warnings)


def _remove_file_within_root(
    candidate: Path,
    root: Path,
    label: str,
    removed: list[str],
    warnings: list[str],
) -> None:
    resolved_root = root.resolve()
    resolved_candidate = candidate.resolve()
    if resolved_candidate == resolved_root or not resolved_candidate.is_relative_to(
        resolved_root
    ):
        warnings.append(f"Skipped unsafe path for {label}.")
        return
    if not resolved_candidate.exists():
        return
    try:
        resolved_candidate.unlink()
        removed.append(label)
    except OSError:
        warnings.append(f"Could not remove {label}.")


def _remove_directory_within_root(
    candidate: Path,
    root: Path,
    label: str,
    removed: list[str],
    warnings: list[str],
) -> None:
    resolved_root = root.resolve()
    resolved_candidate = candidate.resolve()
    if (
        resolved_candidate == resolved_root
        or resolved_candidate.parent != resolved_root
        or not resolved_candidate.is_relative_to(resolved_root)
    ):
        warnings.append(f"Skipped unsafe path for {label}.")
        return
    if not resolved_candidate.exists():
        return
    try:
        shutil.rmtree(resolved_candidate)
        removed.append(label)
    except OSError:
        warnings.append(f"Could not remove {label}.")
