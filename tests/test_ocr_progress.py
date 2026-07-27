"""Tests for OCR progress reporting during page extraction."""

import io
import tempfile
import unittest
from pathlib import Path

import fitz
from PIL import Image

from src.readers.pdf_reader import PDFReader


class FakeOCR:
    def extract_page(self, page):
        return "OCR extracted text"


class FailingOCR:
    def extract_page(self, page):
        raise RuntimeError("tesseract crashed")


def build_mixed_pdf(path):
    """Create a PDF with a text page, a blank page and an image-only page."""
    document = fitz.open()
    document.new_page().insert_text(
        (72, 72),
        "This page contains extractable text.",
    )
    document.new_page()

    image_stream = io.BytesIO()
    Image.new("RGB", (100, 100), "white").save(image_stream, format="PNG")
    image_page = document.new_page()
    image_page.insert_image(
        fitz.Rect(72, 72, 172, 172),
        stream=image_stream.getvalue(),
    )
    document.save(path)
    document.close()


class TestOCRProgressReporting(unittest.TestCase):
    def test_progress_callback_reports_every_page(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "mixed.pdf"
            build_mixed_pdf(path)

            events = []
            reader = PDFReader(str(path))
            reader.get_page_texts(
                ocr_provider=FakeOCR(),
                progress_callback=events.append,
            )
            reader.close()

            self.assertEqual(len(events), 3)
            self.assertEqual(
                [event["page_number"] for event in events],
                [1, 2, 3],
            )
            self.assertTrue(all(e["page_total"] == 3 for e in events))

    def test_progress_callback_flags_only_ocr_pages(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "mixed.pdf"
            build_mixed_pdf(path)

            events = []
            reader = PDFReader(str(path))
            reader.get_page_texts(
                ocr_provider=FakeOCR(),
                progress_callback=events.append,
            )
            reader.close()

            # Text page: never OCR'd. Blank page: skipped. Image page: OCR'd.
            self.assertFalse(events[0]["ocr_attempted"])
            self.assertFalse(events[1]["ocr_attempted"])
            self.assertTrue(events[2]["ocr_attempted"])
            self.assertTrue(events[2]["ocr_used"])

    def test_progress_callback_is_optional(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "mixed.pdf"
            build_mixed_pdf(path)

            reader = PDFReader(str(path))
            pages = reader.get_page_texts(ocr_provider=FakeOCR())
            reader.close()

            self.assertEqual(len(pages), 3)
            self.assertTrue(pages[2]["ocr_used"])

    def test_failing_ocr_page_does_not_abort_the_scan(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "mixed.pdf"
            build_mixed_pdf(path)

            events = []
            reader = PDFReader(str(path))
            pages = reader.get_page_texts(
                ocr_provider=FailingOCR(),
                progress_callback=events.append,
            )
            reader.close()

            # All pages are still returned, and the error is reported.
            self.assertEqual(len(pages), 3)
            self.assertFalse(pages[2]["ocr_used"])
            self.assertIn("tesseract crashed", events[2]["ocr_error"])

    def test_broken_callback_never_breaks_extraction(self):
        def broken_callback(progress):
            raise ValueError("callback bug")

        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "mixed.pdf"
            build_mixed_pdf(path)

            reader = PDFReader(str(path))
            pages = reader.get_page_texts(
                ocr_provider=FakeOCR(),
                progress_callback=broken_callback,
            )
            reader.close()

            self.assertEqual(len(pages), 3)


if __name__ == "__main__":
    unittest.main()
