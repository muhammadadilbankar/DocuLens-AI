import tempfile
import unittest
from pathlib import Path

from PIL import Image

from app.api.routes.documents import _png_dimensions


class PageDimensionTests(unittest.TestCase):
    def test_reads_png_dimensions_without_decoding_the_image(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            image_path = Path(directory) / "page.png"
            Image.new("L", (1600, 2200), 255).save(image_path)

            self.assertEqual(_png_dimensions(image_path, (10, 20)), (1600, 2200))

    def test_uses_fallback_for_a_missing_image(self) -> None:
        self.assertEqual(_png_dimensions(Path("missing.png"), (900, 1200)), (900, 1200))


if __name__ == "__main__":
    unittest.main()
