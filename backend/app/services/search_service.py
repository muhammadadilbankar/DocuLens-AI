import logging
import os
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from app.core.config import Settings
from app.core.database import SessionLocal
from app.models.document import Document, DocumentStatus
from app.models.document_chunk import DocumentChunk
from app.models.page import Page
from app.services.embedding_service import EmbeddingServiceError, LocalEmbeddingService

logger = logging.getLogger(__name__)


class SearchIndexError(RuntimeError):
    pass


@dataclass(frozen=True)
class TextChunk:
    page_number: int
    chunk_index: int
    content: str


@dataclass(frozen=True)
class SearchMatch:
    chunk_id: uuid.UUID
    page_number: int
    chunk_index: int
    content: str
    score: float


def chunk_page_text(
    text: str,
    page_number: int,
    chunk_size_words: int = 120,
    overlap_words: int = 25,
) -> list[TextChunk]:
    if chunk_size_words < 1:
        raise ValueError("Chunk size must be positive.")
    if overlap_words < 0 or overlap_words >= chunk_size_words:
        raise ValueError("Chunk overlap must be smaller than chunk size.")

    words = text.split()
    if not words:
        return []

    chunks: list[TextChunk] = []
    step = chunk_size_words - overlap_words
    for chunk_index, start in enumerate(range(0, len(words), step)):
        content = " ".join(words[start : start + chunk_size_words])
        if content:
            chunks.append(TextChunk(page_number, chunk_index, content))
        if start + chunk_size_words >= len(words):
            break
    return chunks


def process_document_index(document_id: uuid.UUID, settings: Settings) -> None:
    temporary_index_path: Path | None = None
    with SessionLocal() as database:
        document = database.get(Document, document_id)
        if document is None:
            logger.error("Document %s disappeared before indexing", document_id)
            return

        pages = (
            database.query(Page)
            .filter(Page.document_id == document_id)
            .order_by(Page.page_number)
            .all()
        )
        if not pages or any(page.cleaned_text is None for page in pages):
            _mark_failed(database, document, "Cleaned OCR text is required before indexing.")
            return

        document.status = DocumentStatus.INDEXING
        document.error_message = None
        database.commit()

        try:
            chunks = [
                chunk
                for page in pages
                for chunk in chunk_page_text(
                    page.cleaned_text or "",
                    page.page_number,
                    settings.chunk_size_words,
                    settings.chunk_overlap_words,
                )
            ]
            if not chunks:
                raise SearchIndexError("No OCR text was available to build a search index.")

            embeddings = LocalEmbeddingService.encode(
                [chunk.content for chunk in chunks], settings
            )
            try:
                import faiss
            except ImportError as exc:
                raise SearchIndexError("FAISS is not installed.") from exc

            index = faiss.IndexFlatIP(embeddings.shape[1])
            index.add(embeddings)
            index_directory = settings.resolved_search_index_directory.resolve()
            index_directory.mkdir(parents=True, exist_ok=True)
            final_index_path = index_directory / f"{document_id}.faiss"
            temporary_index_path = index_directory / f".{document_id}.{uuid.uuid4().hex}.tmp"
            faiss.write_index(index, str(temporary_index_path))

            database.query(DocumentChunk).filter(
                DocumentChunk.document_id == document_id
            ).delete()
            database.add_all(
                [
                    DocumentChunk(
                        document_id=document_id,
                        page_number=chunk.page_number,
                        content=chunk.content,
                        chunk_index=chunk.chunk_index,
                        vector_position=position,
                    )
                    for position, chunk in enumerate(chunks)
                ]
            )
            database.flush()
            os.replace(temporary_index_path, final_index_path)
            temporary_index_path = None
            document.status = DocumentStatus.COMPLETED
            document.processed_at = datetime.now(timezone.utc)
            database.commit()
        except Exception as exc:
            database.rollback()
            if temporary_index_path is not None:
                temporary_index_path.unlink(missing_ok=True)
            failed_document = database.get(Document, document_id)
            if failed_document is not None:
                _mark_failed(database, failed_document, str(exc)[:2000])
            logger.exception("Search indexing failed for document %s", document_id)


def search_document(
    database,
    document: Document,
    query: str,
    limit: int,
    settings: Settings,
) -> list[SearchMatch]:
    normalized_query = " ".join(query.split())
    if len(normalized_query) < 2:
        raise SearchIndexError("Search query is too short.")
    if document.status != DocumentStatus.COMPLETED:
        raise SearchIndexError("The document search index is not ready.")

    index_path = settings.resolved_search_index_directory.resolve() / f"{document.id}.faiss"
    if not index_path.is_file():
        raise SearchIndexError("The document search index is missing.")

    chunks = (
        database.query(DocumentChunk)
        .filter(DocumentChunk.document_id == document.id)
        .order_by(DocumentChunk.vector_position)
        .all()
    )
    if not chunks:
        raise SearchIndexError("The document has no indexed text chunks.")

    try:
        import faiss

        index = faiss.read_index(str(index_path))
    except ImportError as exc:
        raise SearchIndexError("FAISS is not installed.") from exc
    except RuntimeError as exc:
        raise SearchIndexError("The document search index could not be read.") from exc
    if index.ntotal != len(chunks):
        raise SearchIndexError("The search index does not match its stored chunks.")

    expected_positions = list(range(len(chunks)))
    if [chunk.vector_position for chunk in chunks] != expected_positions:
        raise SearchIndexError("The stored search metadata has invalid vector positions.")

    try:
        query_vector = LocalEmbeddingService.encode([normalized_query], settings)
    except EmbeddingServiceError as exc:
        raise SearchIndexError(str(exc)) from exc
    if index.d != query_vector.shape[1]:
        raise SearchIndexError(
            "The search index was built with a different embedding model. Rebuild it."
        )
    result_limit = min(limit, len(chunks))
    scores, positions = index.search(query_vector, result_limit)
    by_position = {chunk.vector_position: chunk for chunk in chunks}

    matches: list[SearchMatch] = []
    for score, position in zip(scores[0], positions[0], strict=False):
        chunk = by_position.get(int(position))
        if chunk is not None:
            matches.append(
                SearchMatch(
                    chunk_id=chunk.id,
                    page_number=chunk.page_number,
                    chunk_index=chunk.chunk_index,
                    content=chunk.content,
                    score=round(float(score), 6),
                )
            )
    return matches


def _mark_failed(database, document: Document, message: str) -> None:
    document.status = DocumentStatus.FAILED
    document.error_message = message
    database.commit()
