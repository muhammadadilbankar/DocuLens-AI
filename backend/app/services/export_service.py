import csv
import io
import json
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Literal
from uuid import UUID

from app.models.document import Document

ExportFormat = Literal["json", "csv", "txt"]


@dataclass(frozen=True)
class ExportArtifact:
    content: bytes
    media_type: str
    filename: str


def build_document_export(document: Document, export_format: ExportFormat) -> ExportArtifact:
    builders = {
        "json": _build_json_export,
        "csv": _build_csv_export,
        "txt": _build_text_export,
    }
    return builders[export_format](document)


def _build_json_export(document: Document) -> ExportArtifact:
    payload = {
        "document": {
            "id": str(document.id),
            "original_filename": document.original_filename,
            "page_count": document.page_count,
            "status": document.status.value,
            "created_at": _serialize_value(document.created_at),
            "processed_at": _serialize_value(document.processed_at),
        },
        "pages": [
            {
                "id": str(page.id),
                "page_number": page.page_number,
                "raw_text": page.raw_text,
                "cleaned_text": page.cleaned_text,
                "average_ocr_confidence": page.average_ocr_confidence,
                "ocr_blocks": [
                    {
                        "id": str(block.id),
                        "reading_order": block.reading_order,
                        "text": block.text,
                        "confidence": block.confidence,
                        "bounding_box": block.bounding_box,
                    }
                    for block in page.ocr_blocks
                ],
            }
            for page in document.pages
        ],
        "entities": [
            {
                "id": str(entity.id),
                "page_id": str(entity.page_id),
                "page_number": entity.page.page_number,
                "entity_type": entity.entity_type,
                "entity_value": entity.entity_value,
                "confidence": entity.confidence,
                "source": entity.source,
                "bounding_box": entity.bounding_box,
            }
            for entity in document.entities
        ],
        "search_chunks": [
            {
                "id": str(chunk.id),
                "page_number": chunk.page_number,
                "chunk_index": chunk.chunk_index,
                "vector_position": chunk.vector_position,
                "content": chunk.content,
            }
            for chunk in document.chunks
        ],
    }
    content = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
    return ExportArtifact(content, "application/json", _filename(document, "json"))


def _build_csv_export(document: Document) -> ExportArtifact:
    output = io.StringIO(newline="")
    fieldnames = [
        "document_id",
        "original_filename",
        "page_number",
        "entity_type",
        "entity_value",
        "confidence",
        "source",
        "bounding_box",
    ]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    for entity in document.entities:
        writer.writerow(
            {
                "document_id": str(document.id),
                "original_filename": document.original_filename,
                "page_number": entity.page.page_number,
                "entity_type": entity.entity_type,
                "entity_value": entity.entity_value,
                "confidence": "" if entity.confidence is None else entity.confidence,
                "source": entity.source,
                "bounding_box": (
                    "" if entity.bounding_box is None else json.dumps(entity.bounding_box)
                ),
            }
        )
    content = ("\ufeff" + output.getvalue()).encode("utf-8")
    return ExportArtifact(content, "text/csv", _filename(document, "csv"))


def _build_text_export(document: Document) -> ExportArtifact:
    lines = [
        f"Document: {document.original_filename}",
        f"Document ID: {document.id}",
        f"Pages: {document.page_count}",
        "",
    ]
    for page in document.pages:
        lines.extend(
            [
                f"===== PAGE {page.page_number} =====",
                page.cleaned_text or page.raw_text or "[No readable text detected]",
                "",
            ]
        )

    lines.append("===== EXTRACTED ENTITIES =====")
    if document.entities:
        for entity in document.entities:
            lines.append(
                f"Page {entity.page.page_number} | {entity.entity_type} | "
                f"{entity.entity_value} | source={entity.source}"
            )
    else:
        lines.append("[No entities extracted]")
    lines.append("")

    return ExportArtifact(
        "\n".join(lines).encode("utf-8"),
        "text/plain",
        _filename(document, "txt"),
    )


def _filename(document: Document, extension: str) -> str:
    stem = document.original_filename.rsplit(".", 1)[0]
    safe_stem = re.sub(r"[^A-Za-z0-9._-]+", "-", stem).strip("-._") or "document"
    return f"{safe_stem}-export.{extension}"


def _serialize_value(value: datetime | UUID | None) -> str | None:
    if value is None:
        return None
    return value.isoformat() if isinstance(value, datetime) else str(value)
