import re

KEYWORDS_RE = re.compile(r'\b(key\s*words|keywords|index\s*terms|key\s*words\s*and\s*phrases)\b\s*[:.\-]?\s*(.*)', re.IGNORECASE)

def extract_keywords(text: str) -> str:
    """
    Extracts keywords from the PDF text.
    Looks for headers like 'Keywords' or 'Key Words' on the first pages.
    """
    if not text:
        return ""
        
    match = KEYWORDS_RE.search(text)
    if not match:
        return ""
        
    keywords_chunk = match.group(2)
    
    # Clean and split by common delimiters
    # The keywords section usually ends with a newline/newline or period followed by another section
    end_markers = [r'\n\n', r'\r\n\r\n', r'\.', r'Introduction', r'1\s*\.']
    end_pattern = '|'.join(end_markers)
    
    parts = re.split(end_pattern, keywords_chunk, maxsplit=1, flags=re.IGNORECASE)
    keywords_raw = parts[0].strip()
    
    # Split individual keywords, clean up, and rejoin
    keywords_split = re.split(r'[,;]|\band\b', keywords_raw)
    cleaned_keywords = []
    for kw in keywords_split:
        kw_clean = kw.strip().strip('.')
        if kw_clean and len(kw_clean) > 2 and len(kw_clean) < 50:
            # Avoid picking up entire sentences
            if len(kw_clean.split()) <= 5:
                cleaned_keywords.append(kw_clean)
                
    return ", ".join(cleaned_keywords)
