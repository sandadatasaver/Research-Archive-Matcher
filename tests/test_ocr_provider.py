import io
import tempfile
import unittest
from pathlib import Path

import fitz
from PIL import Image

from src.ocr.tesseract_ocr import TesseractOCR
from src.readers.pdf_reader import PDFReader


class FakeOCR:
    def extract_page(self, page):
        return "OCR extracted text"


class TestOCRProvider(unittest.TestCase):
    def test_unavailable_executable_is_reported_safely(self):
        provider = TesseractOCR(executable="C:/does-not-exist/tesseract.exe")
        self.assertFalse(provider.available)

    def test_pdf_reader_can_use_an_ocr_provider(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "image.pdf"
            image_stream = io.BytesIO()
            Image.new("RGB", (100, 100), "white").save(
                image_stream,
                format="PNG",
            )
            document = fitz.open()
            page = document.new_page()
            page.insert_image(
                fitz.Rect(72, 72, 172, 172),
                stream=image_stream.getvalue(),
            )
            document.save(path)
            document.close()

            reader = PDFReader(str(path))
            pages = reader.get_page_texts(ocr_provider=FakeOCR())
            reader.close()

            self.assertEqual(pages[0]["text"], "OCR extracted text")
            self.assertTrue(pages[0]["ocr_used"])


if __name__ == "__main__":
    unittest.main()
