import unittest

from app.services.search_service import chunk_page_text


class SearchServiceTests(unittest.TestCase):
    def test_chunks_text_with_overlap_and_page_metadata(self) -> None:
        text = " ".join(f"word{index}" for index in range(12))

        chunks = chunk_page_text(text, page_number=4, chunk_size_words=5, overlap_words=2)

        self.assertEqual(len(chunks), 4)
        self.assertEqual(chunks[0].content, "word0 word1 word2 word3 word4")
        self.assertEqual(chunks[1].content, "word3 word4 word5 word6 word7")
        self.assertEqual(chunks[-1].content, "word9 word10 word11")
        self.assertTrue(all(chunk.page_number == 4 for chunk in chunks))
        self.assertEqual([chunk.chunk_index for chunk in chunks], [0, 1, 2, 3])

    def test_empty_page_creates_no_chunks(self) -> None:
        self.assertEqual(chunk_page_text(" \n ", page_number=1), [])

    def test_rejects_overlap_equal_to_chunk_size(self) -> None:
        with self.assertRaises(ValueError):
            chunk_page_text("some text", 1, chunk_size_words=10, overlap_words=10)


if __name__ == "__main__":
    unittest.main()
