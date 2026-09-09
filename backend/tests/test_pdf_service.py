import tempfile
import unittest
from pathlib import Path

import pymupdf

from app.services.pdf_service import PdfConversionError, render_pdf_pages


class PdfServiceTests(unittest.TestCase):
    def test_renders_every_page_in_order(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            pdf_path = root / "three-pages.pdf"
            output_directory = root / "rendered"

            with pymupdf.open() as pdf:
                for page_number in range(1, 4):
                    page = pdf.new_page(width=300, height=400)
                    page.insert_text((40, 60), f"Page {page_number}")
                pdf.save(pdf_path)

            pages = render_pdf_pages(pdf_path, output_directory, dpi=72)

            self.assertEqual([page.page_number for page in pages], [1, 2, 3])
            self.assertEqual(
                [page.image_path.name for page in pages],
                ["page_0001.png", "page_0002.png", "page_0003.png"],
            )
            self.assertTrue(all(page.image_path.is_file() for page in pages))
            self.assertTrue(all((page.width, page.height) == (300, 400) for page in pages))

    def test_rejects_unreadable_pdf(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            pdf_path = root / "invalid.pdf"
            pdf_path.write_bytes(b"%PDF- but corrupted")

            with self.assertRaises(PdfConversionError):
                render_pdf_pages(pdf_path, root / "rendered")


if __name__ == "__main__":
    unittest.main()
