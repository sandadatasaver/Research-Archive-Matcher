"""Optional Tesseract OCR provider for image-only PDF pages."""

from __future__ import annotations

import os
import shutil
from pathlib import Path

import fitz


class TesseractUnavailableError(RuntimeError):
    """Raised when Tesseract OCR cannot be used."""


class TesseractOCR:
    """Run Tesseract OCR through pytesseract when available."""

    def __init__(
        self,
        executable: str | None = None,
        language: str = "eng",
        scale: float = 2.0,
    ):
        self.language = language
        self.scale = scale
        self.executable = executable or self._find_executable()
        self._pytesseract = None

        try:
            import pytesseract

            self._pytesseract = pytesseract
            if self.executable:
                pytesseract.pytesseract.tesseract_cmd = self.executable
        except ImportError:
            self._pytesseract = None

    @staticmethod
    def _find_executable() -> str | None:
        candidates = [
            shutil.which("tesseract"),
            r"C:\Program Files\Tesseract-OCR\tesseract.exe",
            str(
                Path.home()
                / "AppData"
                / "Local"
                / "Programs"
                / "Tesseract-OCR"
                / "tesseract.exe"
            ),
            "/usr/bin/tesseract",
            "/usr/local/bin/tesseract",
            "/opt/homebrew/bin/tesseract",
        ]

        for candidate in candidates:
            if candidate and os.path.isfile(candidate):
                return candidate

        return None

    @property
    def available(self) -> bool:
        """Whether both pytesseract and the executable are available."""
        return (
            self._pytesseract is not None
            and self.executable is not None
            and os.path.isfile(self.executable)
        )

    def version(self) -> str:
        """Return the installed Tesseract version."""
        if not self.available:
            raise TesseractUnavailableError(
                "Tesseract OCR is unavailable. Install Tesseract and ensure "
                "pytesseract can find tesseract.exe."
            )

        return str(self._pytesseract.get_tesseract_version())

    def extract_page(self, page) -> str:
        """OCR one PyMuPDF page and return its extracted text."""
        if not self.available:
            raise TesseractUnavailableError(
                "Tesseract OCR is unavailable. Install Tesseract and ensure "
                "pytesseract can find tesseract.exe."
            )

        pixmap = page.get_pixmap(
            matrix=fitz.Matrix(self.scale, self.scale),
            alpha=False,
        )
        from PIL import Image

        pil_image = Image.frombytes(
            "RGB",
            [pixmap.width, pixmap.height],
            pixmap.samples,
        )
        return self._pytesseract.image_to_string(
            pil_image,
            lang=self.language,
        )
