import logging
import uuid
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np

from app.core.config import Settings
from app.core.database import SessionLocal
from app.models.document import Document, DocumentStatus
from app.models.page import Page
from app.services.ocr_service import process_document_ocr

logger = logging.getLogger(__name__)


class ImagePreprocessingError(RuntimeError):
    pass


@dataclass(frozen=True)
class PreprocessedImage:
    image: np.ndarray
    width: int
    height: int
    deskew_angle: float


def preprocess_image(
    image: np.ndarray,
    min_width: int = 1600,
    denoise_strength: int = 7,
    max_deskew_angle: float = 5.0,
) -> PreprocessedImage:
    if image is None or image.size == 0:
        raise ImagePreprocessingError("The page image is empty or unreadable.")

    grayscale = (
        cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if image.ndim == 3 else image.copy()
    )

    if 0 < grayscale.shape[1] < min_width:
        scale = min_width / grayscale.shape[1]
        grayscale = cv2.resize(
            grayscale,
            None,
            fx=scale,
            fy=scale,
            interpolation=cv2.INTER_CUBIC,
        )

    contrast_enhanced = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(
        grayscale
    )
    denoised = cv2.fastNlMeansDenoising(
        contrast_enhanced,
        None,
        h=max(0, denoise_strength),
        templateWindowSize=7,
        searchWindowSize=21,
    )
    thresholded = cv2.adaptiveThreshold(
        denoised,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        31,
        15,
    )
    deskewed, correction_angle = _deskew(thresholded, max_deskew_angle)
    height, width = deskewed.shape[:2]
    return PreprocessedImage(deskewed, width, height, correction_angle)


def preprocess_page_image(
    source_path: Path,
    destination_path: Path,
    settings: Settings,
) -> PreprocessedImage:
    try:
        encoded = np.fromfile(source_path, dtype=np.uint8)
        source = cv2.imdecode(encoded, cv2.IMREAD_COLOR)
    except OSError as exc:
        raise ImagePreprocessingError("The original page image could not be read.") from exc

    result = preprocess_image(
        source,
        min_width=settings.preprocessing_min_width,
        denoise_strength=settings.denoise_strength,
        max_deskew_angle=settings.max_deskew_angle,
    )
    destination_path.parent.mkdir(parents=True, exist_ok=True)
    success, encoded_output = cv2.imencode(".png", result.image)
    if not success:
        raise ImagePreprocessingError("OpenCV could not encode the processed page.")
    try:
        encoded_output.tofile(destination_path)
    except OSError as exc:
        raise ImagePreprocessingError("The processed page image could not be saved.") from exc
    return result


def preprocess_document_pages(document_id: uuid.UUID, settings: Settings) -> None:
    created_paths: list[Path] = []
    preprocessing_succeeded = False
    with SessionLocal() as database:
        document = database.get(Document, document_id)
        if document is None:
            logger.error("Document %s disappeared before preprocessing", document_id)
            return

        pages = (
            database.query(Page)
            .filter(Page.document_id == document_id)
            .order_by(Page.page_number)
            .all()
        )
        if not pages:
            _mark_failed(database, document, "No converted pages are available to preprocess.")
            return

        document.status = DocumentStatus.PREPROCESSING
        document.error_message = None
        database.commit()

        output_directory = (
            settings.resolved_processed_directory / str(document_id) / "preprocessed"
        )
        try:
            for page in pages:
                destination = output_directory / f"page_{page.page_number:04d}.png"
                preprocess_page_image(Path(page.original_image_path), destination, settings)
                created_paths.append(destination.resolve())
                page.preprocessed_image_path = str(destination.resolve())

            document.status = DocumentStatus.OCR_PROCESSING
            database.commit()
            preprocessing_succeeded = True
        except Exception as exc:
            database.rollback()
            _remove_preprocessed_files(created_paths, output_directory)
            failed_document = database.get(Document, document_id)
            if failed_document is not None:
                _mark_failed(database, failed_document, str(exc)[:2000])
            logger.exception("Image preprocessing failed for document %s", document_id)

    if preprocessing_succeeded:
        process_document_ocr(document_id, settings)


def _deskew(image: np.ndarray, maximum_angle: float) -> tuple[np.ndarray, float]:
    foreground_points = np.column_stack(np.where(image < 128))
    if foreground_points.shape[0] < 50:
        return image, 0.0

    points_xy = foreground_points[:, ::-1].astype(np.float32)
    detected_angle = float(cv2.minAreaRect(points_xy)[-1])
    if detected_angle > 45:
        detected_angle -= 90

    correction_angle = -detected_angle
    if abs(correction_angle) < 0.25 or abs(correction_angle) > maximum_angle:
        return image, 0.0

    height, width = image.shape[:2]
    rotation = cv2.getRotationMatrix2D(
        (width / 2.0, height / 2.0), correction_angle, 1.0
    )
    deskewed = cv2.warpAffine(
        image,
        rotation,
        (width, height),
        flags=cv2.INTER_CUBIC,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=255,
    )
    return deskewed, correction_angle


def _mark_failed(database, document: Document, message: str) -> None:
    document.status = DocumentStatus.FAILED
    document.error_message = message
    database.commit()


def _remove_preprocessed_files(paths: list[Path], output_directory: Path) -> None:
    for path in paths:
        path.unlink(missing_ok=True)
    try:
        output_directory.rmdir()
    except OSError:
        pass
