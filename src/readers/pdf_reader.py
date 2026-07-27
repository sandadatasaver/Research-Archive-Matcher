"""Page-aware PDF reading for Research Archive Matcher."""

from __future__ import annotations

import logging
import os

import fitz
from pypdf import PdfReader as PyPdfReader


logger = logging.getLogger(__name__)


class PDFReader:
    """Read PDF text and metadata with a PyMuPDF-first fallback."""

    def __init__(self, file_path: str):
        self.file_path = file_path

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"PDF file not found: {file_path}")

        self.doc = None
        self._load_document()

    def _load_document(self):
        try:
            self.doc = fitz.open(self.file_path)
        except Exception as error:
            logger.warning(
                "PyMuPDF failed to open %s: %s. Trying pypdf.",
                self.file_path,
                error,
            )
            try:
                self.doc = PyPdfReader(self.file_path)
            except Exception as fallback_error:
                logger.error(
                    "Failed to open %s with PyMuPDF and pypdf: %s",
                    self.file_path,
                    fallback_error,
                )
                self.doc = None

    @property
    def page_count(self) -> int:
        if self.doc is None:
            return 0

        if isinstance(self.doc, fitz.Document):
            return len(self.doc)

        if isinstance(self.doc, PyPdfReader):
            return len(self.doc.pages)

        return 0

    def get_page_texts(
        self,
        max_pages: int | None = None,
        ocr_provider=None,
        minimum_text_characters: int = 20,
        progress_callback=None,
    ) -> list[dict]:
        """Extract page text and optionally OCR image-only pages.

        When ``progress_callback`` is supplied it is called once per page with
        a dictionary describing that page's progress. This lets the GUI report
        OCR activity while a long scan is running. A failing callback never
        interrupts extraction.
        """
        if self.doc is None:
            return []

        page_total = self.page_count
        if max_pages is not None:
            page_total = min(page_total, max_pages)

        pages: list[dict] = []

        for page_index in range(page_total):
            try:
                if isinstance(self.doc, fitz.Document):
                    text = self.doc[page_index].get_text()
                elif isinstance(self.doc, PyPdfReader):
                    text = self.doc.pages[page_index].extract_text() or ""
                else:
                    text = ""
            except Exception as error:
                logger.error(
                    "Error extracting page %s from %s: %s",
                    page_index + 1,
                    self.file_path,
                    error,
                )
                text = ""

            ocr_used = False
            ocr_attempted = False
            ocr_error = None

            if ocr_provider is not None and isinstance(self.doc, fitz.Document):
                page = self.doc[page_index]
                text_length = len(" ".join(text.split()))
                has_images = bool(page.get_images(full=True))

                if text_length < minimum_text_characters and has_images:
                    ocr_attempted = True
                    try:
                        ocr_text = ocr_provider.extract_page(page)
                    except Exception as error:
                        # One unreadable page must never abort a whole scan.
                        ocr_error = str(error)
                        logger.error(
                            "OCR failed on page %s of %s: %s",
                            page_index + 1,
                            self.file_path,
                            error,
                        )
                    else:
                        if ocr_text and ocr_text.strip():
                            text = ocr_text
                            ocr_used = True

            page_record = {
                "page_number": page_index + 1,
                "text": text,
                "ocr_used": ocr_used,
            }
            pages.append(page_record)

            if progress_callback is not None:
                try:
                    progress_callback(
                        {
                            "page_number": page_index + 1,
                            "page_total": page_total,
                            "characters": len(" ".join(text.split())),
                            "ocr_attempted": ocr_attempted,
                            "ocr_used": ocr_used,
                            "ocr_error": ocr_error,
                        }
                    )
                except Exception as error:
                    logger.debug("Progress callback failed: %s", error)

        return pages

    def analyze_pages(self, minimum_text_characters: int = 20) -> list[dict]:
        """Identify pages with too little text and likely needing OCR."""
        if minimum_text_characters < 0:
            raise ValueError("minimum_text_characters cannot be negative")

        analysis = []

        page_texts = self.get_page_texts()

        for page in page_texts:
            text_length = len(" ".join(page["text"].split()))
            has_images = False
            page_index = page["page_number"] - 1

            if isinstance(self.doc, fitz.Document):
                try:
                    has_images = bool(
                        self.doc[page_index].get_images(full=True)
                    )
                except Exception as error:
                    logger.debug(
                        "Could not inspect images on page %s: %s",
                        page["page_number"],
                        error,
                    )

            is_blank = text_length == 0 and not has_images

            analysis.append(
                {
                    "page_number": page["page_number"],
                    "text_length": text_length,
                    "has_images": has_images,
                    "is_blank": is_blank,
                    "requires_ocr": (
                        text_length < minimum_text_characters
                        and not is_blank
                    ),
                }
            )

        return analysis

    def get_text(self, max_pages: int | None = None) -> str:
        """Extract and concatenate page text for backward compatibility."""
        return "\n".join(
            page["text"]
            for page in self.get_page_texts(max_pages=max_pages)
        )

    def get_first_page_spans(self):
        """Return font/layout spans from the first page when available."""
        if not self.doc or not isinstance(self.doc, fitz.Document):
            return []

        spans_info = []

        try:
            page = self.doc[0]
            blocks = page.get_text("dict")["blocks"]

            for block in blocks:
                if "lines" not in block:
                    continue

                for line in block["lines"]:
                    for span in line["spans"]:
                        spans_info.append(
                            {
                                "text": span["text"],
                                "size": span["size"],
                                "font": span["font"],
                                "flags": span["flags"],
                                "color": span["color"],
                                "bbox": span["bbox"],
                            }
                        )
        except Exception as error:
            logger.debug("Error getting first-page spans: %s", error)

        return spans_info

    def close(self):
        if self.doc and isinstance(self.doc, fitz.Document):
            self.doc.close()
