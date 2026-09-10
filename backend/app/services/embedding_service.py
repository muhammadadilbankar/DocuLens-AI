import os
import threading
from pathlib import Path
from typing import Any

import numpy as np

from app.core.config import Settings


class EmbeddingServiceError(RuntimeError):
    pass


class LocalEmbeddingService:
    """Loads one local sentence-transformers model and serializes CPU inference."""

    _model: Any = None
    _model_path: Path | None = None
    _initialization_lock = threading.Lock()
    _inference_lock = threading.Lock()

    @classmethod
    def get_model(cls, settings: Settings):
        model_path = settings.resolved_embedding_model_directory.resolve()
        if cls._model is not None and cls._model_path == model_path:
            return cls._model

        with cls._initialization_lock:
            if cls._model is None or cls._model_path != model_path:
                if not model_path.is_dir():
                    raise EmbeddingServiceError(
                        "The local embedding model is missing. Run "
                        "'python -m scripts.download_embedding_model' once while online."
                    )

                os.environ.setdefault("HF_HUB_OFFLINE", "1")
                os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
                try:
                    from sentence_transformers import SentenceTransformer

                    cls._model = SentenceTransformer(
                        str(model_path), device="cpu", local_files_only=True
                    )
                    cls._model_path = model_path
                except (ImportError, OSError, ValueError) as exc:
                    raise EmbeddingServiceError(
                        "The local sentence-transformers model could not be loaded."
                    ) from exc
        return cls._model

    @classmethod
    def encode(cls, texts: list[str], settings: Settings) -> np.ndarray:
        if not texts or any(not text.strip() for text in texts):
            raise EmbeddingServiceError("Embedding input must contain non-empty text.")

        model = cls.get_model(settings)
        with cls._inference_lock:
            vectors = model.encode(
                texts,
                convert_to_numpy=True,
                normalize_embeddings=True,
                show_progress_bar=False,
            )

        embeddings = np.ascontiguousarray(vectors, dtype=np.float32)
        if embeddings.ndim != 2 or embeddings.shape[0] != len(texts):
            raise EmbeddingServiceError("The embedding model returned an invalid matrix.")
        return embeddings
