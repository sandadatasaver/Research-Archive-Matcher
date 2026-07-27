import tempfile
import unittest
from pathlib import Path

import fitz

from src.readers.pdf_reader import PDFReader


class TestPDFReader(unittest.TestCase):
    def test_get_page_texts_preserves_page_numbers(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "pages.pdf"
            document = fitz.open()

            first = document.new_page()
            first.insert_text((72, 72), "First page keyword")

            second = document.new_page()
            second.insert_text((72, 72), "Second page phrase")

            document.save(path)
            document.close()

            reader = PDFReader(str(path))
            pages = reader.get_page_texts()
            reader.close()

            self.assertEqual(len(pages), 2)
            self.assertEqual(pages[0]["page_number"], 1)
            self.assertEqual(pages[1]["page_number"], 2)
            self.assertIn("First page keyword", pages[0]["text"])
            self.assertIn("Second page phrase", pages[1]["text"])

    def test_get_text_remains_backward_compatible(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "single.pdf"
            document = fitz.open()
            page = document.new_page()
            page.insert_text((72, 72), "Backward compatible text")
            document.save(path)
            document.close()

            reader = PDFReader(str(path))
            text = reader.get_text()
            reader.close()

            self.assertIn("Backward compatible text", text)


if __name__ == "__main__":
    unittest.main()
