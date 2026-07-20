import re
import urllib.request
import json
import logging
from src.readers.pdf_reader import PDFReader
from src.extractors.title import extract_title
from src.extractors.doi import extract_doi
from src.extractors.authors import extract_authors
from src.extractors.abstract import extract_abstract
from src.extractors.keywords import extract_keywords

logger = logging.getLogger(__name__)

YEAR_RE = re.compile(r'\b(19\d{2}|20[0-2]\d)\b')

def extract_year(text: str) -> str:
    """
    Extracts publication year from text by looking for standard year patterns.
    """
    if not text:
        return ""
    # Find all 4-digit years in the first page text
    years = YEAR_RE.findall(text)
    if not years:
        return ""
    # Return the first year that looks reasonable (e.g. <= 2026)
    for year in years:
        y_int = int(year)
        if 1900 <= y_int <= 2026:
            return str(y_int)
    return ""

def identify_journal(text: str) -> str:
    """
    Identifies the journal name if present in text.
    """
    if not text:
        return ""
    # Look for "Journal of ..." or "International Journal of ..." or similar
    match = re.search(r'\b((?:International\s+)?Journal\s+of\s+[A-Za-z\s]+)\b', text, re.IGNORECASE)
    if match:
        journal = match.group(1).strip()
        # Clean up trailing spaces or punctuation
        journal = re.sub(r'[\d,.\-;\s]+$', '', journal)
        if len(journal) > 10 and len(journal) < 100:
            return journal
    return ""

def classify_document_type(reader: PDFReader, text: str) -> str:
    """
    Classifies the PDF into:
    - Research Article
    - Book / Monograph
    - Table of Contents
    - Conference Paper
    - Report / Other
    - Unreadable
    """
    if not reader or reader.page_count == 0:
        return "Unreadable"
        
    if not text or len(text.strip()) < 100:
        return "Unreadable"
        
    page_count = reader.page_count
    text_lower = text.lower()
    
    # Check for Table of Contents
    toc_indicators = [r'table of contents', r'\bcontents\b', r'\bindex\b']
    toc_count = sum(1 for ind in toc_indicators if re.search(ind, text_lower))
    dots_count = len(re.findall(r'\.{5,}', text))
    if (toc_count >= 2 or (toc_count >= 1 and dots_count > 5)) and page_count < 25:
        return "Table of Contents"
        
    # Check for Book
    if page_count > 100 or "isbn" in text_lower:
        if page_count > 50:
            return "Book"
            
    # Check for Research Article vs Conference Paper
    has_references = "references" in text_lower or "bibliography" in text_lower or "literature cited" in text_lower
    has_abstract = "abstract" in text_lower or "summary" in text_lower
    
    if has_references and has_abstract:
        if page_count <= 15:
            # Check for conference keywords
            conf_keywords = ["proceedings", "conference", "symposium", "workshop"]
            if any(kw in text_lower for kw in conf_keywords):
                return "Conference Paper"
            return "Research Article"
        else:
            return "Research Article"
            
    if has_references or has_abstract:
        return "Research Article"
        
    return "Report / Other"

def query_crossref_api(doi: str) -> dict:
    """
    Queries Crossref API to retrieve rich metadata for a given DOI.
    Fails gracefully if offline or network connection is blocked.
    """
    if not doi:
        return {}
    
    url = f"https://api.crossref.org/works/{doi}"
    headers = {
        'User-Agent': 'ResearchArchiveMatcher/1.0 (mailto:sandadatasaver@arena.ai)'
    }
    req = urllib.request.Request(url, headers=headers)
    
    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            if response.status == 200:
                data = json.loads(response.read().decode('utf-8'))
                item = data.get("message", {})
                
                # Parse title
                title_list = item.get("title", [])
                title = title_list[0] if title_list else ""
                
                # Parse authors
                author_list = item.get("author", [])
                authors = []
                for a in author_list:
                    given = a.get("given", "")
                    family = a.get("family", "")
                    if given and family:
                        authors.append(f"{given} {family}")
                    elif family:
                        authors.append(family)
                authors_str = ", ".join(authors)
                
                # Parse year
                pub_date = item.get("published-print", item.get("published-online", {}))
                date_parts = pub_date.get("date-parts", [[]])[0]
                year = str(date_parts[0]) if date_parts else ""
                
                # Parse journal
                container_list = item.get("container-title", [])
                journal = container_list[0] if container_list else ""
                
                # Parse publisher
                publisher = item.get("publisher", "")
                
                return {
                    "title": title,
                    "authors": authors_str,
                    "year": year,
                    "journal": journal,
                    "publisher": publisher,
                    "doi": doi,
                    "source": "Crossref"
                }
    except Exception as e:
        logger.debug(f"Crossref lookup failed for DOI {doi}: {e}")
    
    return {}

class MetadataExtractor:
    """
    Main metadata extraction orchestrator.
    """
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.reader = PDFReader(file_path)

    def extract(self, online_enrich: bool = False) -> dict:
        """
        Extracts metadata from the PDF document.
        :param online_enrich: Whether to enrich metadata via Crossref DOI lookup.
        """
        metadata = {
            "file_name": self.reader.file_path.split('/')[-1],
            "file_path": self.reader.file_path,
            "title": "",
            "authors": "",
            "doi": "",
            "journal": "",
            "year": "",
            "abstract": "",
            "keywords": "",
            "document_type": "Unreadable",
            "page_count": self.reader.page_count,
            "enrich_source": "Offline"
        }
        
        try:
            # 1. Read first pages text
            first_page_text = self.reader.get_text(max_pages=1)
            full_text_sample = self.reader.get_text(max_pages=3)
            
            # If no text could be read, classify as Unreadable immediately
            if not first_page_text:
                metadata["document_type"] = "Unreadable"
                return metadata
                
            # 2. Extract DOI
            doi = extract_doi(full_text_sample)
            metadata["doi"] = doi
            
            # 3. Extract Title
            title = extract_title(self.reader)
            metadata["title"] = title
            
            # 4. Extract Abstract
            abstract = extract_abstract(full_text_sample)
            metadata["abstract"] = abstract
            
            # 5. Extract Authors
            authors = extract_authors(first_page_text, title, abstract)
            metadata["authors"] = authors
            
            # 6. Extract Keywords
            keywords = extract_keywords(full_text_sample)
            metadata["keywords"] = keywords
            
            # 7. Extract Year
            year = extract_year(first_page_text)
            metadata["year"] = year
            
            # 8. Identify Journal
            journal = identify_journal(first_page_text)
            metadata["journal"] = journal
            
            # 9. Classify Document Type
            doc_type = classify_document_type(self.reader, full_text_sample)
            metadata["document_type"] = doc_type
            
            # 10. Perform Optional Online Enrichment
            if online_enrich and doi:
                online_meta = query_crossref_api(doi)
                if online_meta:
                    metadata["title"] = online_meta.get("title") or metadata["title"]
                    metadata["authors"] = online_meta.get("authors") or metadata["authors"]
                    metadata["year"] = online_meta.get("year") or metadata["year"]
                    metadata["journal"] = online_meta.get("journal") or metadata["journal"]
                    metadata["enrich_source"] = "Crossref"
                    
        except Exception as e:
            logger.error(f"Error during metadata extraction for {self.file_path}: {e}")
        finally:
            self.reader.close()
            
        return metadata
