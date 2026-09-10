import csv
import io
import json
import unittest
import uuid
from datetime import datetime, timezone
from types import SimpleNamespace

from app.models.document import DocumentStatus
from app.services.export_service import build_document_export


class ExportServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        page_id = uuid.UUID("20000000-0000-4000-8000-000000000001")
        page = SimpleNamespace(
            id=page_id,
            page_number=1,
            raw_text="Amount: INR 250,000",
            cleaned_text="Amount: INR 250,000",
            average_ocr_confidence=0.94,
            ocr_blocks=[
                SimpleNamespace(
                    id=uuid.UUID("30000000-0000-4000-8000-000000000001"),
                    reading_order=0,
                    text="INR 250,000",
                    confidence=0.96,
                    bounding_box=[[1, 2], [3, 2], [3, 4], [1, 4]],
                )
            ],
        )
        entity = SimpleNamespace(
            id=uuid.UUID("40000000-0000-4000-8000-000000000001"),
            page_id=page_id,
            page=page,
            entity_type="MONEY",
            entity_value="INR 250,000",
            confidence=0.96,
            source="regex",
            bounding_box=[[1, 2], [3, 2], [3, 4], [1, 4]],
        )
        chunk = SimpleNamespace(
            id=uuid.UUID("50000000-0000-4000-8000-000000000001"),
            page_number=1,
            chunk_index=0,
            vector_position=0,
            content="Amount: INR 250,000",
        )
        self.document = SimpleNamespace(
            id=uuid.UUID("10000000-0000-4000-8000-000000000001"),
            original_filename="Loan Statement (Final).pdf",
            page_count=1,
            status=DocumentStatus.COMPLETED,
            created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
            processed_at=datetime(2026, 1, 2, tzinfo=timezone.utc),
            pages=[page],
            entities=[entity],
            chunks=[chunk],
        )

    def test_json_contains_ocr_entities_and_search_traceability(self) -> None:
        artifact = build_document_export(self.document, "json")
        payload = json.loads(artifact.content)

        self.assertEqual(artifact.filename, "Loan-Statement-Final-export.json")
        self.assertEqual(payload["pages"][0]["ocr_blocks"][0]["confidence"], 0.96)
        self.assertEqual(payload["entities"][0]["page_number"], 1)
        self.assertEqual(payload["search_chunks"][0]["vector_position"], 0)

    def test_csv_is_excel_friendly_and_preserves_commas(self) -> None:
        artifact = build_document_export(self.document, "csv")
        rows = list(csv.DictReader(io.StringIO(artifact.content.decode("utf-8-sig"))))

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["entity_value"], "INR 250,000")
        self.assertEqual(rows[0]["page_number"], "1")

    def test_text_export_contains_page_text_and_entity_appendix(self) -> None:
        artifact = build_document_export(self.document, "txt")
        content = artifact.content.decode("utf-8")

        self.assertIn("===== PAGE 1 =====", content)
        self.assertIn("Amount: INR 250,000", content)
        self.assertIn("Page 1 | MONEY | INR 250,000 | source=regex", content)


if __name__ == "__main__":
    unittest.main()
