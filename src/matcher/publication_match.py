import os
import re
import logging
from src.readers.word_reader import WordReader
from src.readers.excel_reader import ExcelReader
from src.extractors.doi import extract_doi
from src.matcher.fuzzy_match import compute_similarity

logger = logging.getLogger(__name__)

class PublicationMatcher:
    """
    Orchestrates the matching of a list of target publications
    against the indexed PDFs in the database.
    """
    def __init__(self, db, threshold: float = 70.0):
        self.db = db
        self.threshold = threshold

    def _load_targets(self, file_path: str) -> list:
        """
        Loads targets from Word, Excel, or text files.
        Returns a list of dicts, each containing:
          - "raw_text": original full citation or row text
          - "title": parsed/inferred title
          - "doi": parsed/inferred DOI
          - "authors": parsed/inferred authors (optional)
        """
        targets = []
        ext = os.path.splitext(file_path)[1].lower()
        
        if ext == ".docx":
            reader = WordReader(file_path)
            lines = reader.read_lines()
            for line in lines:
                doi = extract_doi(line)
                # If there's a DOI, we might clean the text around it, or just use the full line
                targets.append({
                    "raw_text": line,
                    "title": line,  # In Word, the whole line represents the citation/title
                    "doi": doi,
                    "authors": ""
                })
                
        elif ext in [".xlsx", ".xls"]:
            reader = ExcelReader(file_path)
            records = reader.read_records()
            for rec in records:
                # Build a raw text summary of the row
                raw_text = " | ".join(f"{k}: {v}" for k, v in rec.items() if v)
                
                # Look for columns that might contain title, doi, authors
                title = ""
                doi = ""
                authors = ""
                
                # Check keys (case-insensitive)
                for k, v in rec.items():
                    k_lower = str(k).lower()
                    val_str = str(v).strip()
                    if not val_str:
                        continue
                    if "title" in k_lower or "article" in k_lower or "publication" in k_lower:
                        title = val_str
                    elif "doi" in k_lower:
                        doi = extract_doi(val_str) or val_str
                    elif "author" in k_lower or "writer" in k_lower:
                        authors = val_str
                
                # If we couldn't find a specific title column, use the longest field as the title
                if not title and rec:
                    string_fields = [str(v) for v in rec.values() if isinstance(v, (str, int, float)) and v]
                    if string_fields:
                        title = max(string_fields, key=len)
                
                # Ensure DOI is clean
                if not doi:
                    doi = extract_doi(raw_text)
                    
                targets.append({
                    "raw_text": raw_text,
                    "title": title or raw_text,
                    "doi": doi.lower().strip() if doi else "",
                    "authors": authors
                })
                
        else: # Fallback to text file line by line
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    for line in f:
                        line_clean = line.strip()
                        if line_clean:
                            doi = extract_doi(line_clean)
                            targets.append({
                                "raw_text": line_clean,
                                "title": line_clean,
                                "doi": doi,
                                "authors": ""
                            })
            except Exception as e:
                logger.error(f"Failed to read targets text file {file_path}: {e}")
                
        return targets

    def match(self, targets_file_path: str) -> dict:
        """
        Performs matching against the indexed database.
        Returns a dict:
          - "matched": list of dicts with target, matched doc metadata, and score.
          - "unmatched": list of target dicts that didn't match.
        """
        targets = self._load_targets(targets_file_path)
        indexed_docs = self.db.get_all_documents()
        
        matched_results = []
        unmatched_results = []
        
        for target in targets:
            best_match = None
            best_score = 0.0
            match_method = "None"
            
            # --- 1. Match by DOI (100% confidence if match found) ---
            if target["doi"]:
                # Find matching doc in indexed list
                for doc in indexed_docs:
                    if doc["doi"] and doc["doi"].lower().strip() == target["doi"].lower().strip():
                        best_match = doc
                        best_score = 100.0
                        match_method = "DOI Exact Match"
                        break
            
            # --- 2. Match by Title similarity (if no DOI match was found) ---
            if not best_match and target["title"]:
                for doc in indexed_docs:
                    if doc["title"]:
                        score = compute_similarity(target["title"], doc["title"])
                        if score > best_score:
                            best_score = score
                            best_match = doc
                            match_method = "Fuzzy Title Match"
            
            # Check if best match is above threshold
            if best_match and best_score >= self.threshold:
                matched_results.append({
                    "target_raw": target["raw_text"],
                    "target_title": target["title"],
                    "target_doi": target["doi"],
                    "matched_file_name": best_match["file_name"],
                    "matched_file_path": best_match["file_path"],
                    "matched_title": best_match["title"],
                    "matched_authors": best_match["authors"],
                    "matched_doi": best_match["doi"],
                    "matched_journal": best_match["journal"],
                    "matched_year": best_match["year"],
                    "matched_type": best_match["document_type"],
                    "score": round(best_score, 1),
                    "method": match_method
                })
            else:
                unmatched_results.append({
                    "target_raw": target["raw_text"],
                    "target_title": target["title"],
                    "target_doi": target["doi"],
                    "best_candidate_title": best_match["title"] if best_match else "",
                    "best_candidate_score": round(best_score, 1) if best_match else 0.0
                })
                
        return {
            "matched": matched_results,
            "unmatched": unmatched_results
        }
