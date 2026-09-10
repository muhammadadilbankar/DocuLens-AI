import unittest

from app.core.database import Base
from app.models import Document, DocumentChunk, Entity, OcrBlock, Page  # noqa: F401


class PersistenceSchemaTests(unittest.TestCase):
    def test_all_child_foreign_keys_cascade_on_delete(self) -> None:
        expected_cascades = {
            ("pages", "document_id"),
            ("ocr_blocks", "page_id"),
            ("entities", "document_id"),
            ("entities", "page_id"),
            ("document_chunks", "document_id"),
        }
        actual_cascades = {
            (table.name, column.name)
            for table in Base.metadata.tables.values()
            for column in table.columns
            for foreign_key in column.foreign_keys
            if foreign_key.ondelete == "CASCADE"
        }

        self.assertTrue(expected_cascades.issubset(actual_cascades))

    def test_common_lookup_indexes_are_declared(self) -> None:
        index_names = {
            index.name
            for table in Base.metadata.tables.values()
            for index in table.indexes
        }

        self.assertIn("ix_documents_created_at", index_names)
        self.assertIn("ix_entities_document_created_id", index_names)
        self.assertIn("ix_pages_document_id", index_names)
        self.assertIn("ix_document_chunks_document_id", index_names)


if __name__ == "__main__":
    unittest.main()
