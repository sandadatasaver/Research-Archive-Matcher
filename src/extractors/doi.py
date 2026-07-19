import re

# Standard DOI regex pattern
DOI_REGEX = re.compile(r'\b10\.\d{4,9}/[-._;()/:A-Z0-9]+\b', re.IGNORECASE)

def extract_dois(text: str) -> list:
    """
    Extracts all DOIs from text, returning a list of unique DOIs in lowercase.
    """
    if not text:
        return []
    
    found = DOI_REGEX.findall(text)
    # Deduplicate and clean (remove trailing dots, common in text extraction)
    cleaned = []
    for doi in found:
        # DOI cannot end with certain punctuation marks due to regex edge cases
        doi_clean = doi.strip().rstrip('.,;)')
        if doi_clean.lower() not in cleaned:
            cleaned.append(doi_clean.lower())
    
    return cleaned

def extract_doi(text: str) -> str:
    """
    Returns the first DOI found in the text, or an empty string.
    """
    dois = extract_dois(text)
    return dois[0] if dois else ""
