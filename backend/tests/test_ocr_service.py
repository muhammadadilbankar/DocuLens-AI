import tempfile
import unittest
from pathlib import Path

import numpy as np

from app.core.config import Settings
from app.services.ocr_service import recognize_page


class FakeOcrEngine:
    def predict(self, _image_path):
        return [
            {
                "res": {
                    "rec_texts": ["  Loan Amount  ", "ignored"],
                    "rec_scores": np.array([0.96, 0.12]),
                    "rec_polys": np.array(
                        [
                            [[10, 20], [210, 20], [210, 55], [10, 55]],
                            [[1, 1], [2, 1], [2, 2], [1, 2]],
                        ]
                    ),
                }
            }
        ]


class OcrServiceTests(unittest.TestCase):
    def test_normalizes_paddle_result_and_filters_low_confidence_text(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            image_path = Path(directory) / "page.png"
            image_path.touch()

            result = recognize_page(
                image_path,
                page_number=3,
                settings=Settings(ocr_min_confidence=0.25),
                engine=FakeOcrEngine(),
            )

            self.assertEqual(result.page_number, 3)
            self.assertEqual(result.full_text, "Loan Amount")
            self.assertEqual(result.cleaned_text, "Loan Amount")
            self.assertAlmostEqual(result.average_confidence, 0.96)
            self.assertEqual(len(result.blocks), 1)
            self.assertEqual(
                result.blocks[0].bounding_box,
                [[10.0, 20.0], [210.0, 20.0], [210.0, 55.0], [10.0, 55.0]],
            )

    def test_empty_detection_is_a_completed_zero_confidence_page(self) -> None:
        class EmptyEngine:
            def predict(self, _image_path):
                return [{"res": {"rec_texts": [], "rec_scores": [], "rec_polys": []}}]

        with tempfile.TemporaryDirectory() as directory:
            image_path = Path(directory) / "blank.png"
            image_path.touch()
            result = recognize_page(image_path, 1, Settings(), engine=EmptyEngine())

            self.assertEqual(result.blocks, [])
            self.assertEqual(result.full_text, "")
            self.assertEqual(result.average_confidence, 0.0)


if __name__ == "__main__":
    unittest.main()
