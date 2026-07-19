import fitz  # PyMuPDF
from pypdf import PdfReader as PyPdfReader
import os
import logging

logger = logging.getLogger(__name__)

class PDFReader:
    """
    A robust class to read PDF files, supporting PyMuPDF (fitz) primarily,
    with a fallback to pypdf.
    """
    def __init__(self, file_path):
        self.file_path = file_path
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"PDF file not found: {file_path}")
        self.doc = None
        self._load_document()

    def _load_document(self):
        try:
            self.doc = fitz.open(self.file_path)
        except Exception as e:
            logger.warning(f"PyMuPDF failed to open {self.file_path}: {e}. Trying fallback pypdf...")
            try:
                self.doc = PyPdfReader(self.file_path)
            except Exception as e2:
                logger.error(f"Failed to open PDF {self.file_path} with both fitz and pypdf: {e2}")
                self.doc = None

    @property
    def page_count(self) -> int:
        if not self.doc:
            return 0
        if isinstance(self.doc, fitz.Document):
            return len(self.doc)
        elif isinstance(self.doc, PyPdfReader):
            return len(self.doc.pages)
        return 0

    def get_text(self, max_pages=None) -> str:
        """
        Extract raw text from the document.
        :param max_pages: Maximum number of pages to read (None for all).
        """
        if not self.doc:
            return ""
        
        text_list = []
        pages_to_read = self.page_count
        if max_pages is not None:
            pages_to_read = min(pages_to_read, max_pages)

        try:
            if isinstance(self.doc, fitz.Document):
                for page_num in range(pages_to_read):
                    page = self.doc[page_num]
                    text_list.append(page.get_text())
            elif isinstance(self.doc, PyPdfReader):
                for page_num in range(pages_to_read):
                    page = self.doc.pages[page_num]
                    text_list.append(page.extract_text() or "")
        except Exception as e:
            logger.error(f"Error extracting text from {self.file_path}: {e}")
        
        return "\n".join(text_list)

    def get_first_page_spans(self):
        """
        Retrieve spans with font-size metadata from the first page (only available in PyMuPDF).
        """
        if not self.doc or not isinstance(self.doc, fitz.Document):
            return []
        
        spans_info = []
        try:
            page = self.doc[0]
            blocks = page.get_text("dict")["blocks"]
            for b in blocks:
                if "lines" in b:
                    for l in b["lines"]:
                        for s in l["spans"]:
                            spans_info.append({
                                "text": s["text"],
                                "size": s["size"],
                                "font": s["font"],
                                "flags": s["flags"],
                                "color": s["color"],
                                "bbox": s["bbox"]
                            })
        except Exception as e:
            logger.debug(f"Error getting page spans: {e}")
        return spans_info

    def close(self):
        if self.doc and isinstance(self.doc, fitz.Document):
            self.doc.close()
