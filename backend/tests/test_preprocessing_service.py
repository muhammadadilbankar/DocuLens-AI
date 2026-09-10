import tempfile
import unittest
from pathlib import Path

import cv2
import numpy as np

from app.core.config import Settings
from app.services.preprocessing_service import preprocess_image, preprocess_page_image


class PreprocessingServiceTests(unittest.TestCase):
    def test_pipeline_returns_binary_grayscale_and_upscales_small_pages(self) -> None:
        image = np.full((180, 240, 3), 245, dtype=np.uint8)
        cv2.putText(
            image,
            "Loan 250000",
            (15, 95),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (25, 25, 25),
            2,
            cv2.LINE_AA,
        )

        result = preprocess_image(image, min_width=480)

        self.assertEqual(result.image.ndim, 2)
        self.assertEqual(result.width, 480)
        self.assertEqual(result.height, 360)
        self.assertTrue(set(np.unique(result.image)).issubset({0, 255}))
        self.assertLessEqual(abs(result.deskew_angle), 5.0)

    def test_file_pipeline_preserves_original_and_writes_separate_output(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source_path = root / "original.png"
            destination_path = root / "preprocessed" / "page_0001.png"
            source = np.full((200, 300, 3), 255, dtype=np.uint8)
            cv2.putText(source, "ARCIL", (30, 110), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
            cv2.imwrite(str(source_path), source)
            original_bytes = source_path.read_bytes()

            preprocess_page_image(
                source_path,
                destination_path,
                Settings(preprocessing_min_width=300),
            )

            self.assertTrue(destination_path.is_file())
            self.assertEqual(source_path.read_bytes(), original_bytes)
            processed = cv2.imread(str(destination_path), cv2.IMREAD_GRAYSCALE)
            self.assertIsNotNone(processed)


if __name__ == "__main__":
    unittest.main()
