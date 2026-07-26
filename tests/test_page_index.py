import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock

import fitz

from src.indexer.database import Database
from src.readers.pdf_reader import PDFReader


class TestPageIndex(unittest.TestCase):
    def test_page_texts_are_stored_and_searchable(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            pdf_path = Path(temp_dir) / "papers.pdf"
            db_path = Path(temp_dir) / "index.db"
            document = fitz.open()

            first = document.new_page()
            first.insert_text((72, 72), "PowerShell automation research")
            second = document.new_page()
            second.insert_text((72, 72), "A different sentence")
            document.save(pdf_path)
            document.close()

            db = Database(str(db_path))
            db.calculate_file_hash = MagicMock(return_value="hash-1")
            db.add_document(
                {
                    "file_name": "papers.pdf",
                    "file_path": str(pdf_path),
                    "title": "PowerShell automation research",
                    "authors": "Author",
                    "page_count": 2,
                }
            )

            pages = PDFReader(str(pdf_path)).get_page_texts()
            stored = db.replace_page_texts(str(pdf_path), pages)
            results = db.search_pages("PowerShell automation", exact_phrase=True)

            self.assertEqual(stored, 2)
            self.assertEqual(db.get_page_count(str(pdf_path)), 2)
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0]["page_number"], 1)
            self.assertIn("PowerShell", results[0]["page_text"])


if __name__ == "__main__":
    unittest.main()
