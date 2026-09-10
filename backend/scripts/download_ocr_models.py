from app.core.config import get_settings
from app.services.ocr_service import PaddleOcrEngine


if __name__ == "__main__":
    settings = get_settings()
    PaddleOcrEngine.get(settings)
    print("PaddleOCR models are installed and ready for offline inference.")
