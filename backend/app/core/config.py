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


@lru_cache
def get_settings() -> Settings:
    return Settings()
