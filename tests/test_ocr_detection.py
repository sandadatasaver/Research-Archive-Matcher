import io
import tempfile
import unittest
from pathlib import Path

import fitz
from PIL import Image

from src.readers.pdf_reader import PDFReader


class TestOCRDetection(unittest.TestCase):
    def test_analyze_pages_distinguishes_blank_and_image_pages(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "ocr.pdf"
            document = fitz.open()
            document.new_page().insert_text(
                (72, 72),
                "This page contains extractable text.",
            )
            document.new_page()

            image_stream = io.BytesIO()
            Image.new("RGB", (100, 100), "white").save(
                image_stream,
                format="PNG",
            )
            image_page = document.new_page()
            image_page.insert_image(
                fitz.Rect(72, 72, 172, 172),
                stream=image_stream.getvalue(),
            )
            document.save(path)
            document.close()

            reader = PDFReader(str(path))
            analysis = reader.analyze_pages(minimum_text_characters=20)
            reader.close()

            self.assertEqual(len(analysis), 3)
            self.assertFalse(analysis[0]["requires_ocr"])
            self.assertTrue(analysis[1]["is_blank"])
            self.assertFalse(analysis[1]["requires_ocr"])
            self.assertTrue(analysis[2]["has_images"])
            self.assertTrue(analysis[2]["requires_ocr"])


if __name__ == "__main__":
    unittest.main()
