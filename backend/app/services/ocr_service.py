import logging
import os
import threading
import uuid
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.core.config import Settings
from app.core.database import SessionLocal
from app.models.document import Document, DocumentStatus
from app.models.ocr_block import OcrBlock
from app.models.page import Page
from app.services.entity_service import process_document_entities

logger = logging.getLogger(__name__)


class OcrProcessingError(RuntimeError):
    pass


@dataclass(frozen=True)
class OcrBlockResult:
    text: str
    confidence: float
    bounding_box: list[list[float]]


@dataclass(frozen=True)
class OcrPageResult:
    page_number: int
    blocks: list[OcrBlockResult]
    full_text: str
    cleaned_text: str
    average_confidence: float


class PaddleOcrEngine:
    _engine: Any = None
    _initialization_lock = threading.Lock()
    _inference_lock = threading.Lock()

    @classmethod
    def get(cls, settings: Settings):
        if cls._engine is not None:
            return cls._engine

        with cls._initialization_lock:
            if cls._engine is None:
                model_cache = settings.resolved_model_cache_directory
                model_cache.mkdir(parents=True, exist_ok=True)
                os.environ.setdefault("PADDLE_PDX_CACHE_HOME", str(model_cache))
                os.environ.setdefault(
                    "PADDLE_PDX_MODEL_SOURCE", settings.ocr_model_source
                )
                # Model names and cache paths are explicit, so startup does not need
                # an online model-host availability check.
                os.environ.setdefault("PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK", "True")
                try:
                    from paddleocr import PaddleOCR
                except ImportError as exc:
                    raise OcrProcessingError(
                        "PaddleOCR is not installed. Install the Phase 5 dependencies."
                    ) from exc

                options: dict[str, Any] = {
                    "device": settings.ocr_device,
                    "enable_mkldnn": settings.ocr_enable_mkldnn,
                    "text_detection_model_name": settings.ocr_detection_model,
                    "text_recognition_model_name": settings.ocr_recognition_model,
                    "text_rec_score_thresh": settings.ocr_min_confidence,
                    "use_doc_orientation_classify": False,
                    "use_doc_unwarping": False,
                    "use_textline_orientation": False,
                }
                if settings.ocr_detection_model_dir:
                    options["text_detection_model_dir"] = str(
                        settings.ocr_detection_model_dir
                    )
                if settings.ocr_recognition_model_dir:
                    options["text_recognition_model_dir"] = str(
                        settings.ocr_recognition_model_dir
                    )
                try:
                    cls._engine = PaddleOCR(**options)
                except Exception as exc:
                    raise OcrProcessingError(
                        "PaddleOCR models could not be initialized. Download them once while online or configure local model directories."
                    ) from exc
        return cls._engine

    @classmethod
    def predict(cls, engine, image_path: Path):
        with cls._inference_lock:
            return list(engine.predict(str(image_path)))


def recognize_page(
    image_path: Path,
    page_number: int,
    settings: Settings,
    engine=None,
) -> OcrPageResult:
    if not image_path.is_file():
        raise OcrProcessingError("The preprocessed page image is missing.")

    active_engine = engine or PaddleOcrEngine.get(settings)
    try:
        predictions = PaddleOcrEngine.predict(active_engine, image_path)
    except Exception as exc:
        raise OcrProcessingError(
            f"PaddleOCR inference failed for page {page_number}."
        ) from exc

    blocks: list[OcrBlockResult] = []
    for prediction in predictions:
        payload = _prediction_payload(prediction)
        texts = _to_list(payload.get("rec_texts"))
        scores = _to_list(payload.get("rec_scores"))
        polygons = _to_list(payload.get("rec_polys"))

        for text, score, polygon in zip(texts, scores, polygons, strict=False):
            normalized_text = str(text).strip()
            if not normalized_text:
                continue
            confidence = float(score)
            if confidence < settings.ocr_min_confidence:
                continue
            blocks.append(
                OcrBlockResult(
                    text=normalized_text,
                    confidence=confidence,
                    bounding_box=_normalize_polygon(polygon),
                )
            )

    full_text = "\n".join(block.text for block in blocks)
    cleaned_text = "\n".join(
        " ".join(line.split()) for line in full_text.splitlines() if line.strip()
    )
    average_confidence = (
        sum(block.confidence for block in blocks) / len(blocks) if blocks else 0.0
    )
    return OcrPageResult(
        page_number=page_number,
        blocks=blocks,
        full_text=full_text,
        cleaned_text=cleaned_text,
        average_confidence=average_confidence,
    )


def process_document_ocr(document_id: uuid.UUID, settings: Settings) -> None:
    ocr_succeeded = False
    with SessionLocal() as database:
        document = database.get(Document, document_id)
        if document is None:
            logger.error("Document %s disappeared before OCR", document_id)
            return

        pages = (
            database.query(Page)
            .filter(Page.document_id == document_id)
            .order_by(Page.page_number)
            .all()
        )
        if not pages or any(not page.preprocessed_image_path for page in pages):
            _mark_failed(database, document, "Preprocessed pages are required before OCR.")
            return

        document.status = DocumentStatus.OCR_PROCESSING
        document.error_message = None
        database.commit()

        try:
            engine = PaddleOcrEngine.get(settings)
            for page in pages:
                result = recognize_page(
                    Path(page.preprocessed_image_path),
                    page.page_number,
                    settings,
                    engine,
                )
                database.query(OcrBlock).filter(OcrBlock.page_id == page.id).delete()
                database.add_all(
                    [
                        OcrBlock(
                            page_id=page.id,
                            text=block.text,
                            confidence=block.confidence,
                            bounding_box=block.bounding_box,
                            reading_order=index,
                        )
                        for index, block in enumerate(result.blocks)
                    ]
                )
                page.raw_text = result.full_text
                page.cleaned_text = result.cleaned_text
                page.average_ocr_confidence = result.average_confidence
                database.commit()

            document.status = DocumentStatus.EXTRACTING_ENTITIES
            database.commit()
            ocr_succeeded = True
        except Exception as exc:
            database.rollback()
            failed_document = database.get(Document, document_id)
            if failed_document is not None:
                _mark_failed(database, failed_document, str(exc)[:2000])
            logger.exception("OCR failed for document %s", document_id)

    if ocr_succeeded:
        process_document_entities(document_id, settings)


def _prediction_payload(prediction: Any) -> Mapping[str, Any]:
    if isinstance(prediction, Mapping):
        raw = prediction
    elif hasattr(prediction, "json"):
        raw = prediction.json
        if callable(raw):
            raw = raw()
    elif hasattr(prediction, "to_dict"):
        raw = prediction.to_dict()
    else:
        try:
            raw = dict(prediction)
        except (TypeError, ValueError) as exc:
            raise OcrProcessingError("PaddleOCR returned an unsupported result format.") from exc

    if not isinstance(raw, Mapping):
        raise OcrProcessingError("PaddleOCR returned an unsupported result payload.")
    nested = raw.get("res")
    return nested if isinstance(nested, Mapping) else raw


def _to_list(value: Any) -> list:
    if value is None:
        return []
    if hasattr(value, "tolist"):
        return value.tolist()
    return list(value)


def _normalize_polygon(polygon: Any) -> list[list[float]]:
    points = _to_list(polygon)
    if len(points) != 4:
        raise OcrProcessingError("PaddleOCR returned an invalid bounding polygon.")
    return [[round(float(x), 2), round(float(y), 2)] for x, y in points]


def _mark_failed(database, document: Document, message: str) -> None:
    document.status = DocumentStatus.FAILED
    document.error_message = message
    database.commit()
