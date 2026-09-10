from collections.abc import Generator
from pathlib import Path

from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import get_settings


class Base(DeclarativeBase):
    pass


settings = get_settings()
engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db() -> Generator[Session, None, None]:
    database = SessionLocal()
    try:
        yield database
    finally:
        database.close()


def verify_database_revision() -> None:
    backend_root = Path(__file__).resolve().parents[2]
    alembic_config = Config(str(backend_root / "alembic.ini"))
    migrations = ScriptDirectory.from_config(alembic_config)
    expected_heads = set(migrations.get_heads())
    with engine.connect() as connection:
        current_heads = set(MigrationContext.configure(connection).get_current_heads())
    if current_heads != expected_heads:
        current = ", ".join(sorted(current_heads)) or "unversioned"
        expected = ", ".join(sorted(expected_heads))
        raise RuntimeError(
            f"Database revision is {current}; expected {expected}. "
            "Run 'alembic upgrade head' from the backend directory."
        )
