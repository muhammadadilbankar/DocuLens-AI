import tempfile
import unittest
import uuid
from datetime import UTC, datetime
from io import BytesIO
from pathlib import Path

from starlette.datastructures import Headers, UploadFile

from app.core.config import Settings
from app.services.document_service import (
    UploadValidationError,
    _safe_original_filename,
    store_uploaded_document,
)


class FakeSession:
    def __init__(self) -> None:
        self.added = None
        self.committed = False
        self.rolled_back = False

    def add(self, instance) -> None:
        self.added = instance

    def commit(self) -> None:
        self.committed = True

    def refresh(self, instance) -> None:
        instance.id = uuid.uuid4()
        instance.created_at = datetime.now(UTC)

    def rollback(self) -> None:
        self.rolled_back = True


def make_upload(filename: str, content: bytes, content_type: str) -> UploadFile:
    return UploadFile(
        BytesIO(content),
        filename=filename,
        headers=Headers({"content-type": content_type}),
    )


class DocumentServiceTests(unittest.IsolatedAsyncioTestCase):
    def test_filename_is_reduced_to_its_basename(self) -> None:
        self.assertEqual(_safe_original_filename("../../statements/loan.pdf"), "loan.pdf")
        self.assertEqual(_safe_original_filename(r"C:\fake\loan.PDF"), "loan.PDF")

    async def test_valid_pdf_is_stored_under_a_uuid_filename(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            settings = Settings(upload_directory=Path(directory))
            database = FakeSession()
            upload = make_upload(
                "borrower statement.pdf",
                b"%PDF-1.7\nsmall fixture",
                "application/pdf",
            )

            document = await store_uploaded_document(upload, database, settings)

            self.assertTrue(database.committed)
            self.assertEqual(document.original_filename, "borrower statement.pdf")
            self.assertEqual(Path(document.stored_filename).suffix, ".pdf")
            uuid.UUID(Path(document.stored_filename).stem)
            self.assertEqual(Path(document.file_path).read_bytes(), b"%PDF-1.7\nsmall fixture")

    async def test_spoofed_pdf_is_rejected_and_removed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            settings = Settings(upload_directory=Path(directory))
            upload = make_upload("not-really.pdf", b"plain text", "application/pdf")

            with self.assertRaises(UploadValidationError):
                await store_uploaded_document(upload, FakeSession(), settings)

            self.assertEqual(list(Path(directory).iterdir()), [])


if __name__ == "__main__":
    unittest.main()
