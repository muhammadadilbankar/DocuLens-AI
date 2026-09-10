import tempfile
import unittest
import uuid
from pathlib import Path
from types import SimpleNamespace

from sqlalchemy.exc import SQLAlchemyError

from app.core.config import Settings
from app.services.document_service import DocumentDeletionError, delete_stored_document


class FakeDeleteSession:
    def __init__(self, fail_commit: bool = False) -> None:
        self.deleted = None
        self.fail_commit = fail_commit
        self.rolled_back = False

    def delete(self, instance) -> None:
        self.deleted = instance

    def commit(self) -> None:
        if self.fail_commit:
            raise SQLAlchemyError("database unavailable")

    def rollback(self) -> None:
        self.rolled_back = True


class DocumentDeletionTests(unittest.TestCase):
    def test_deletes_database_record_and_all_scoped_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            document_id = uuid.uuid4()
            settings = Settings(
                upload_directory=root / "uploads",
                processed_directory=root / "processed",
                search_index_directory=root / "indexes",
            )
            uploaded_pdf = settings.resolved_upload_directory / f"{document_id}.pdf"
            processed_page = (
                settings.resolved_processed_directory
                / str(document_id)
                / "original"
                / "page_0001.png"
            )
            search_index = (
                settings.resolved_search_index_directory / f"{document_id}.faiss"
            )
            temporary_index = (
                settings.resolved_search_index_directory
                / f".{document_id}.interrupted.tmp"
            )
            for path in (uploaded_pdf, processed_page, search_index, temporary_index):
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(b"fixture")

            document = SimpleNamespace(id=document_id, file_path=str(uploaded_pdf))
            database = FakeDeleteSession()
            result = delete_stored_document(document, database, settings)

            self.assertIs(database.deleted, document)
            self.assertFalse(uploaded_pdf.exists())
            self.assertFalse((settings.resolved_processed_directory / str(document_id)).exists())
            self.assertFalse(search_index.exists())
            self.assertFalse(temporary_index.exists())
            self.assertEqual(result.cleanup_warnings, [])
            self.assertEqual(
                set(result.removed_artifacts),
                {
                    "uploaded PDF",
                    "processed page images",
                    "FAISS search index",
                    "temporary FAISS index",
                },
            )

    def test_refuses_to_remove_an_uploaded_file_outside_storage_root(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            outside_file = root / "outside.pdf"
            outside_file.write_bytes(b"preserve me")
            settings = Settings(
                upload_directory=root / "uploads",
                processed_directory=root / "processed",
                search_index_directory=root / "indexes",
            )
            document = SimpleNamespace(id=uuid.uuid4(), file_path=str(outside_file))

            result = delete_stored_document(document, FakeDeleteSession(), settings)

            self.assertTrue(outside_file.exists())
            self.assertIn("Skipped unsafe path for uploaded PDF.", result.cleanup_warnings)

    def test_keeps_files_when_database_deletion_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            document_id = uuid.uuid4()
            settings = Settings(upload_directory=root / "uploads")
            uploaded_pdf = settings.resolved_upload_directory / f"{document_id}.pdf"
            uploaded_pdf.parent.mkdir(parents=True)
            uploaded_pdf.write_bytes(b"preserve me")
            database = FakeDeleteSession(fail_commit=True)
            document = SimpleNamespace(id=document_id, file_path=str(uploaded_pdf))

            with self.assertRaises(DocumentDeletionError):
                delete_stored_document(document, database, settings)

            self.assertTrue(uploaded_pdf.exists())
            self.assertTrue(database.rolled_back)


if __name__ == "__main__":
    unittest.main()
