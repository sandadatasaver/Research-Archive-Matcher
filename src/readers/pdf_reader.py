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

    def get_page_texts(self, max_pages: int | None = None) -> list[dict]:
        """Extract text page by page with one-based page numbers."""
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

            pages.append({"page_number": page_index + 1, "text": text})

        return pages

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
