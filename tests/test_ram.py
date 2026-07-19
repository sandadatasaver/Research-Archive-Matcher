import unittest
import os
import sqlite3
import pandas as pd
from unittest.mock import MagicMock

# Import our modules
from src.matcher.fuzzy_match import compute_similarity, is_match
from src.extractors.title import clean_title, is_boilerplate, extract_title_heuristic
from src.extractors.doi import extract_doi, extract_dois
from src.extractors.authors import clean_author_name, extract_authors
from src.extractors.abstract import extract_abstract
from src.extractors.keywords import extract_keywords
from src.indexer.database import Database
from src.matcher.publication_match import PublicationMatcher
from src.reports.excel_report import ExcelReporter
from src.reports.word_report import WordReporter
from src.reports.html_report import HTMLReporter

class TestResearchArchiveMatcher(unittest.TestCase):
    
    def test_title_cleaning(self):
        self.assertEqual(clean_title("   Dynamic systems!  "), "Dynamic systems!")
        self.assertEqual(clean_title("[Research] My Paper Title.  "), "Research] My Paper Title.")
        self.assertTrue(is_boilerplate("Journal of Medical Sciences"))
        self.assertTrue(is_boilerplate("ISSN 1234-5678"))
        self.assertFalse(is_boilerplate("Newcastle Disease Virus in Chickens"))

    def test_doi_extraction(self):
        text = "This is a paper with DOI: 10.1016/j.jvirological.2015.02.011 and some other text."
        self.assertEqual(extract_doi(text), "10.1016/j.jvirological.2015.02.011")
        self.assertEqual(extract_dois(text), ["10.1016/j.jvirological.2015.02.011"])
        
    def test_fuzzy_matching(self):
        s1 = "Newcastle Disease in Poultry"
        s2 = "newcastle disease in poultry."
        s3 = "Different Paper Entirely"
        self.assertTrue(is_match(s1, s2))
        self.assertFalse(is_match(s1, s3, threshold=50))
        self.assertGreater(compute_similarity(s1, s2), 90.0)

    def test_author_cleaning(self):
        self.assertEqual(clean_author_name("John Doe1,*"), "John Doe")
        self.assertEqual(clean_author_name("†Alice Smith"), "Alice Smith")

    def test_abstract_extraction(self):
        text = "Some headers here\nABSTRACT: This is the body of the abstract. It describes vaccine studies.\nIntroduction: This is the start of the paper."
        abstract = extract_abstract(text)
        self.assertEqual(abstract, "This is the body of the abstract. It describes vaccine studies.")

    def test_keywords_extraction(self):
        text = "Title here\nKeywords: poultry, Newcastle disease, vaccine.\n1. Introduction"
        kws = extract_keywords(text)
        self.assertEqual(kws, "poultry, Newcastle disease, vaccine")

    def test_database_operations(self):
        db_path = "test_index.db"
        if os.path.exists(db_path):
            os.remove(db_path)
            
        db = Database(db_path)
        # Mock file hash to prevent warning
        db.calculate_file_hash = MagicMock(return_value="fake_hash")
        
        self.assertEqual(db.get_document_count(), 0)
        
        meta = {
            "file_name": "paper1.pdf",
            "file_path": "path/to/paper1.pdf",
            "title": "Studies on Newcastle Disease",
            "authors": "John Doe, Jane Smith",
            "doi": "10.1016/1234",
            "journal": "Journal of Virology",
            "year": "2024",
            "abstract": "An abstract here...",
            "keywords": "newcastle, virus",
            "document_type": "Research Article",
            "page_count": 8
        }
        
        db.add_document(meta)
        self.assertEqual(db.get_document_count(), 1)
        
        search_res = db.search("Newcastle")
        self.assertEqual(len(search_res), 1)
        self.assertEqual(search_res[0]["title"], "Studies on Newcastle Disease")
        
        # Test clear
        db.clear()
        self.assertEqual(db.get_document_count(), 0)
        
        if os.path.exists(db_path):
            os.remove(db_path)

    def test_reporting(self):
        # Mock results
        results = {
            "matched": [
                {
                    "target_raw": "John Doe. Studies on Newcastle Disease (2024)",
                    "target_title": "Studies on Newcastle Disease",
                    "target_doi": "10.1016/1234",
                    "matched_file_name": "paper1.pdf",
                    "matched_file_path": "path/to/paper1.pdf",
                    "matched_title": "Studies on Newcastle Disease",
                    "matched_authors": "John Doe, Jane Smith",
                    "matched_doi": "10.1016/1234",
                    "matched_journal": "Journal of Virology",
                    "matched_year": "2024",
                    "matched_type": "Research Article",
                    "score": 100.0,
                    "method": "DOI Exact Match"
                }
            ],
            "unmatched": [
                {
                    "target_raw": "Unmatched Citation 2026",
                    "target_title": "Unmatched Citation 2026",
                    "target_doi": "",
                    "best_candidate_title": "Studies on Newcastle Disease",
                    "best_candidate_score": 15.2
                }
            ]
        }
        
        db_stats = {"total_docs": 1}
        
        # Output paths
        excel_matched = "report.xlsx"
        excel_unmatched = "unmatched.xlsx"
        excel_dups = "duplicates.xlsx"
        word_report = "matching_report.docx"
        html_report = "matching_report.html"
        
        # Clean up existing files
        for path in [excel_matched, excel_unmatched, excel_dups, word_report, html_report]:
            if os.path.exists(path):
                os.remove(path)
                
        # Generate reports
        ExcelReporter.export_matching_results(results, ".")
        ExcelReporter.export_duplicates_report([], [], ".")
        WordReporter.generate_report(results, db_stats, word_report)
        HTMLReporter.generate_report(results, db_stats, html_report)
        
        # Check files exist
        self.assertTrue(os.path.exists(excel_matched))
        self.assertTrue(os.path.exists(excel_unmatched))
        self.assertTrue(os.path.exists(excel_dups))
        self.assertTrue(os.path.exists(word_report))
        self.assertTrue(os.path.exists(html_report))
        
        # Clean up
        for path in [excel_matched, excel_unmatched, excel_dups, word_report, html_report]:
            if os.path.exists(path):
                os.remove(path)

if __name__ == "__main__":
    unittest.main()
