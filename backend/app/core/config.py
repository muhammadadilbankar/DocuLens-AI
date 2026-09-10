from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "DocuLens AI API"
    environment: str = "development"
    debug: bool = False
    frontend_url: str = "http://127.0.0.1:5173"
    database_url: str = (
        "postgresql+psycopg://postgres:postgres@127.0.0.1:5432/doculens"
    )
    upload_directory: Path = Path("uploads")
    processed_directory: Path = Path("processed")
    max_upload_size_mb: int = 50
    pdf_render_dpi: int = 150
    preprocessing_min_width: int = 1600
    denoise_strength: int = 7
    max_deskew_angle: float = 5.0
    ocr_device: str = "cpu"
    ocr_enable_mkldnn: bool = False
    ocr_detection_model: str = "PP-OCRv5_mobile_det"
    ocr_recognition_model: str = "en_PP-OCRv5_mobile_rec"
    ocr_min_confidence: float = 0.25
    model_cache_directory: Path = Path("models_cache")
    ocr_model_source: str = "BOS"
    ocr_detection_model_dir: Path | None = None
    ocr_recognition_model_dir: Path | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="DOCULENS_",
        extra="ignore",
    )

    @property
    def cors_origins(self) -> list[str]:
        configured = self.frontend_url.rstrip("/")
        origins = {configured}

        # Vite is commonly opened using either hostname during development.
        if configured == "http://127.0.0.1:5173":
            origins.add("http://localhost:5173")
        elif configured == "http://localhost:5173":
            origins.add("http://127.0.0.1:5173")

        return sorted(origins)

    @property
    def resolved_upload_directory(self) -> Path:
        if self.upload_directory.is_absolute():
            return self.upload_directory
        backend_root = Path(__file__).resolve().parents[2]
        return backend_root / self.upload_directory

    @property
    def max_upload_size_bytes(self) -> int:
        return self.max_upload_size_mb * 1024 * 1024

    @property
    def resolved_processed_directory(self) -> Path:
        if self.processed_directory.is_absolute():
            return self.processed_directory
        backend_root = Path(__file__).resolve().parents[2]
        return backend_root / self.processed_directory

    @property
    def resolved_model_cache_directory(self) -> Path:
        if self.model_cache_directory.is_absolute():
            return self.model_cache_directory
        backend_root = Path(__file__).resolve().parents[2]
        return backend_root / self.model_cache_directory


@lru_cache
def get_settings() -> Settings:
    return Settings()
