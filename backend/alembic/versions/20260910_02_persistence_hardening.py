"""Add persistence hardening indexes and constraint names.

Revision ID: 20260910_02
Revises: 20260910_01
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260910_02"
down_revision: str | None = "20260910_01"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE documents RENAME CONSTRAINT "
        "documents_stored_filename_key TO uq_documents_stored_filename"
    )
    op.create_index("ix_documents_created_at", "documents", ["created_at"])
    op.create_index(
        "ix_entities_document_created_id",
        "entities",
        ["document_id", "created_at", "id"],
    )


def downgrade() -> None:
    op.drop_index("ix_entities_document_created_id", table_name="entities")
    op.drop_index("ix_documents_created_at", table_name="documents")
    op.execute(
        "ALTER TABLE documents RENAME CONSTRAINT "
        "uq_documents_stored_filename TO documents_stored_filename_key"
    )
