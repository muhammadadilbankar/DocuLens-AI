from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "DocuLens AI API"
    environment: str = "development"
    debug: bool = False
    frontend_url: str = "http://127.0.0.1:5173"

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


@lru_cache
def get_settings() -> Settings:
    return Settings()

