from app.core.config import get_settings


if __name__ == "__main__":
    from sentence_transformers import SentenceTransformer

    settings = get_settings()
    destination = settings.resolved_embedding_model_directory.resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    model = SentenceTransformer(
        settings.embedding_model,
        device="cpu",
        cache_folder=str(settings.resolved_model_cache_directory.resolve()),
    )
    model.save_pretrained(str(destination))
    print(f"Embedding model saved for offline use at {destination}")
