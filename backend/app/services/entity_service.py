import logging
import re
import threading
import uuid
from dataclasses import dataclass
from typing import Any

from app.core.config import Settings
from app.core.database import SessionLocal
from app.models.document import Document, DocumentStatus
from app.models.entity import Entity
from app.models.page import Page

logger = logging.getLogger(__name__)


class EntityExtractionError(RuntimeError):
    pass


@dataclass(frozen=True)
class ExtractedEntity:
    entity_type: str
    entity_value: str
    confidence: float | None
    source: str
    bounding_box: list[list[float]] | None
    start: int
    end: int


@dataclass(frozen=True)
class RegexRule:
    entity_type: str
    pattern: re.Pattern[str]
    value_group: str | int = 0


REGEX_RULES = (
    RegexRule(
        "GSTIN",
        re.compile(r"\b\d{2}[A-Z]{5}\d{4}[A-Z][1-9A-Z]Z[0-9A-Z]\b", re.I),
    ),
    RegexRule("PAN", re.compile(r"\b[A-Z]{5}\d{4}[A-Z]\b", re.I)),
    RegexRule("IFSC", re.compile(r"\b[A-Z]{4}0[A-Z0-9]{6}\b", re.I)),
    RegexRule(
        "EMAIL",
        re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I),
    ),
    RegexRule(
        "PHONE",
        re.compile(r"(?<!\d)(?:\+91[\s-]?)?[6-9]\d{9}(?!\d)"),
    ),
    RegexRule(
        "DATE",
        re.compile(
            r"\b(?:\d{1,2}[/-]\d{1,2}[/-](?:\d{2}|\d{4})|"
            r"\d{1,2}\s+(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|"
            r"May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|"
            r"Nov(?:ember)?|Dec(?:ember)?)\s+\d{4})\b",
            re.I,
        ),
    ),
    RegexRule(
        "MONEY",
        re.compile(
            r"(?:₹|Rs\.?|INR)\s*[\d,]+(?:\.\d{1,2})?"
            r"|\b[\d,]+(?:\.\d{1,2})?\s*(?:lakh|lakhs|crore|crores)\b",
            re.I,
        ),
    ),
    RegexRule("PERCENT", re.compile(r"\b\d+(?:\.\d+)?\s*%")),
    RegexRule(
        "ACCOUNT_NUMBER",
        re.compile(
            r"\b(?:loan\s+)?account(?:\s+(?:number|no\.?))?\s*[:#-]?\s*"
            r"(?P<value>[A-Z0-9][A-Z0-9/-]{4,})",
            re.I,
        ),
        "value",
    ),
    RegexRule(
        "PERSON",
        re.compile(
            r"(?im)\b(?:borrower|applicant|customer)\s*(?:name)?\s*:\s*"
            r"(?P<value>[A-Z][A-Za-z .'-]{2,80})$"
        ),
        "value",
    ),
    RegexRule(
        "ORGANIZATION",
        re.compile(
            r"(?im)\b(?:lender|bank|creditor|financial institution)\s*"
            r"(?:name)?\s*:\s*(?P<value>[A-Z][A-Za-z0-9 &.,'-]{2,100})$"
        ),
        "value",
    ),
    RegexRule(
        "PIN_CODE",
        re.compile(r"\b(?:pin|postal\s+code)\s*[:#-]?\s*(?P<value>\d{6})\b", re.I),
        "value",
    ),
)

SPACY_ENTITY_TYPES = {
    "PERSON": "PERSON",
    "ORG": "ORGANIZATION",
    "GPE": "LOCATION",
    "LOC": "LOCATION",
    "FAC": "LOCATION",
    "DATE": "DATE",
    "MONEY": "MONEY",
    "PERCENT": "PERCENT",
}

FIELD_LABELS = {
    "ACCOUNT",
    "APPLICANT",
    "BORROWER",
    "DATE",
    "GSTIN",
    "IFSC",
    "INR",
    "LENDER",
    "PAN",
}


class SpacyNerEngine:
    _engine: Any = None
    _model_name: str | None = None
    _initialization_lock = threading.Lock()
    _inference_lock = threading.Lock()

    @classmethod
    def get(cls, settings: Settings):
        if cls._engine is not None and cls._model_name == settings.spacy_model:
            return cls._engine

        with cls._initialization_lock:
            if cls._engine is None or cls._model_name != settings.spacy_model:
                try:
                    import spacy

                    cls._engine = spacy.load(
                        settings.spacy_model,
                        disable=["tagger", "parser", "attribute_ruler", "lemmatizer"],
                    )
                    cls._model_name = settings.spacy_model
                except (ImportError, OSError) as exc:
                    raise EntityExtractionError(
                        f"spaCy model '{settings.spacy_model}' is not installed. "
                        "Install the Phase 6 dependencies before processing."
                    ) from exc
        return cls._engine

    @classmethod
    def analyze(cls, engine, text: str):
        with cls._inference_lock:
            return engine(text)


def extract_entities(text: str, ocr_blocks: list[Any], nlp: Any) -> list[ExtractedEntity]:
    if not text.strip():
        return []

    candidates: list[ExtractedEntity] = []
    for rule in REGEX_RULES:
        for match in rule.pattern.finditer(text):
            start, end = match.span(rule.value_group)
            value = match.group(rule.value_group).strip(" \t\r\n:;,.#")
            if value:
                candidates.append(
                    ExtractedEntity(
                        entity_type=rule.entity_type,
                        entity_value=value,
                        confidence=1.0,
                        source="REGEX",
                        bounding_box=_bounding_box_for_span(start, end, ocr_blocks),
                        start=start,
                        end=end,
                    )
                )

    document = SpacyNerEngine.analyze(nlp, text)
    for item in document.ents:
        entity_type = SPACY_ENTITY_TYPES.get(item.label_)
        value = item.text.strip(" \t\r\n:;,.#")
        # OCR lines represent separate visual regions. Reject a model span that
        # crosses a line boundary because it cannot be traced to one coherent value.
        if (
            entity_type
            and value
            and value.upper() not in FIELD_LABELS
            and "\n" not in item.text
            and "\r" not in item.text
        ):
            candidates.append(
                ExtractedEntity(
                    entity_type=entity_type,
                    entity_value=value,
                    confidence=None,
                    source="SPACY",
                    bounding_box=_bounding_box_for_span(
                        item.start_char, item.end_char, ocr_blocks
                    ),
                    start=item.start_char,
                    end=item.end_char,
                )
            )

    candidates.sort(key=lambda entity: (entity.start, entity.source != "REGEX", entity.end))
    results: list[ExtractedEntity] = []
    seen: set[tuple[str, str, int, int]] = set()
    for candidate in candidates:
        key = (
            candidate.entity_type,
            " ".join(candidate.entity_value.casefold().split()),
            candidate.start,
            candidate.end,
        )
        if key not in seen:
            seen.add(key)
            results.append(candidate)
    return results


def process_document_entities(document_id: uuid.UUID, settings: Settings) -> None:
    with SessionLocal() as database:
        document = database.get(Document, document_id)
        if document is None:
            logger.error("Document %s disappeared before entity extraction", document_id)
            return

        pages = (
            database.query(Page)
            .filter(Page.document_id == document_id)
            .order_by(Page.page_number)
            .all()
        )
        if not pages or any(page.raw_text is None for page in pages):
            _mark_failed(database, document, "OCR text is required before entity extraction.")
            return

        document.status = DocumentStatus.EXTRACTING_ENTITIES
        document.error_message = None
        database.commit()

        try:
            nlp = SpacyNerEngine.get(settings)
            database.query(Entity).filter(Entity.document_id == document_id).delete()
            database.commit()
            for page in pages:
                for result in extract_entities(page.raw_text or "", page.ocr_blocks, nlp):
                    database.add(
                        Entity(
                            document_id=document_id,
                            page_id=page.id,
                            entity_type=result.entity_type,
                            entity_value=result.entity_value,
                            confidence=result.confidence,
                            source=result.source,
                            bounding_box=result.bounding_box,
                        )
                    )
                database.commit()

            document.status = DocumentStatus.INDEXING
            database.commit()
        except Exception as exc:
            database.rollback()
            failed_document = database.get(Document, document_id)
            if failed_document is not None:
                _mark_failed(database, failed_document, str(exc)[:2000])
            logger.exception("Entity extraction failed for document %s", document_id)


def _bounding_box_for_span(
    start: int, end: int, ocr_blocks: list[Any]
) -> list[list[float]] | None:
    cursor = 0
    polygons: list[list[list[float]]] = []
    for block in ocr_blocks:
        block_text = block.text.strip()
        block_start = cursor
        block_end = block_start + len(block_text)
        if start < block_end and end > block_start:
            polygons.append(block.bounding_box)
        cursor = block_end + 1

    points = [point for polygon in polygons for point in polygon]
    if not points:
        return None
    minimum_x = min(float(point[0]) for point in points)
    minimum_y = min(float(point[1]) for point in points)
    maximum_x = max(float(point[0]) for point in points)
    maximum_y = max(float(point[1]) for point in points)
    return [
        [minimum_x, minimum_y],
        [maximum_x, minimum_y],
        [maximum_x, maximum_y],
        [minimum_x, maximum_y],
    ]


def _mark_failed(database, document: Document, message: str) -> None:
    document.status = DocumentStatus.FAILED
    document.error_message = message
    database.commit()
