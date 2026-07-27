import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock

import fitz

from src.indexer.database import Database
from src.readers.pdf_reader import PDFReader
from src.search.page_search import PageSearchService


class TestPageSearch(unittest.TestCase):
    def test_exact_phrase_survives_pdf_line_breaks(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "index.db"
            db = Database(str(db_path))
            db.add_document(
                {
                    "file_name": "line-break.pdf",
                    "file_path": "line-break.pdf",
                    "title": "Line Break Test",
                    "page_count": 1,
                }
            )
            db.replace_page_texts(
                "line-break.pdf",
                [{
                    "page_number": 1,
                    "text": "PowerShell\nautomation is useful",
                }],
            )

            results = PageSearchService(db).search(
                "PowerShell automation",
                exact_phrase=True,
            )

            self.assertEqual(len(results), 1)
            self.assertEqual(results[0].score, 100.0)

    def test_page_search_returns_page_and_score(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            pdf_path = Path(temp_dir) / "search.pdf"
            db_path = Path(temp_dir) / "index.db"
            document = fitz.open()
            page = document.new_page()
            page.insert_text((72, 72), "PowerShell automation for research")
            document.new_page().insert_text((72, 72), "Unrelated content")
            document.save(pdf_path)
            document.close()

            db = Database(str(db_path))
            db.calculate_file_hash = MagicMock(return_value="hash-search")
            db.add_document(
                {
                    "file_name": "search.pdf",
                    "file_path": str(pdf_path),
                    "title": "PowerShell Research",
                    "page_count": 2,
                }
            )
            db.replace_page_texts(
                str(pdf_path),
                PDFReader(str(pdf_path)).get_page_texts(),
            )

            results = PageSearchService(db).search(
                "PowerShell automation",
                exact_phrase=True,
            )

            self.assertEqual(len(results), 1)
            self.assertEqual(results[0].page_number, 1)
            self.assertEqual(results[0].score, 100.0)
            self.assertEqual(results[0].match_type, "exact phrase")
            self.assertIn("PowerShell", results[0].snippet)


if __name__ == "__main__":
    unittest.main()
