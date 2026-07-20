import re
from src.readers.pdf_reader import PDFReader

BOILERPLATE_PATTERNS = [
    re.compile(r'journal of', re.IGNORECASE),
    re.compile(r'proceedings of', re.IGNORECASE),
    re.compile(r'volume \d+', re.IGNORECASE),
    re.compile(r'vol\.\s*\d+', re.IGNORECASE),
    re.compile(r'no\.\s*\d+', re.IGNORECASE),
    re.compile(r'issn\s*[\d-]+', re.IGNORECASE),
    re.compile(r'https?://', re.IGNORECASE),
    re.compile(r'www\.', re.IGNORECASE),
    re.compile(r'research\s*article', re.IGNORECASE),
    re.compile(r'original\s*paper', re.IGNORECASE),
    re.compile(r'review\s*article', re.IGNORECASE),
    re.compile(r'doi:', re.IGNORECASE),
    re.compile(r'page\s*\d+', re.IGNORECASE),
    re.compile(r'pages?\s*\d+\s*-\s*\d+', re.IGNORECASE),
    re.compile(r'accepted', re.IGNORECASE),
    re.compile(r'published', re.IGNORECASE),
    re.compile(r'received', re.IGNORECASE),
    re.compile(r'copyright', re.IGNORECASE),
    re.compile(r'all rights reserved', re.IGNORECASE),
]

def is_boilerplate(text: str) -> bool:
    """
    Checks if a line of text is likely journal boilerplate.
    """
    clean_text = text.strip()
    if not clean_text:
        return True
    
    # Check against compiled patterns
    for pattern in BOILERPLATE_PATTERNS:
        if pattern.search(clean_text):
            return True
            
    # If it's purely numbers and symbols (like page numbers or dates)
    if re.match(r'^[0-9\s.,\-\/()]+$', clean_text):
        return True
        
    return False

def clean_title(title: str) -> str:
    """
    Cleans up the extracted title string.
    """
    if not title:
        return ""
    # Replace multiple spaces/newlines with a single space
    cleaned = re.sub(r'\s+', ' ', title)
    cleaned = cleaned.strip()
    
    # Remove leading/trailing non-alphanumeric chars (except quotes/parentheses)
    cleaned = re.sub(r'^[^a-zA-Z0-9"\']+', '', cleaned)
    cleaned = re.sub(r'[^a-zA-Z0-9"\'.!?)]+$', '', cleaned)
    
    return cleaned

def extract_title_from_spans(spans: list) -> str:
    """
    Extracts the title using font size analysis from PyMuPDF page spans.
    """
    if not spans:
        return ""

    # Filter out empty or obviously boilerplate spans
    valid_spans = []
    for s in spans:
        text = s["text"].strip()
        if not text or len(text) < 4:
            continue
        # Also filter out extremely long spans (which are likely abstract/paragraphs)
        if len(text) > 250:
            continue
        if is_boilerplate(text):
            continue
        valid_spans.append(s)

    if not valid_spans:
        return ""

    # Sort spans by font size descending
    sorted_spans = sorted(valid_spans, key=lambda x: x["size"], reverse=True)
    
    # Take the largest font size
    max_size = sorted_spans[0]["size"]
    
    # If the largest font size is too small (e.g. < 8), font sizes might not be loaded correctly
    if max_size < 8:
        return ""

    # We want to grab all spans that have a size close to max_size (e.g. within 1.5 points)
    # and occur in the top-to-bottom reading flow.
    title_spans = []
    for s in valid_spans:
        if abs(s["size"] - max_size) <= 1.5:
            title_spans.append(s)

    if not title_spans:
        return ""

    # Re-order the selected spans based on their vertical (top) then horizontal (left) position
    # bbox format: (x0, y0, x1, y1)
    title_spans_sorted = sorted(title_spans, key=lambda s: (round(s["bbox"][1], 1), s["bbox"][0]))
    
    # Join adjacent spans. If they are separated by too much vertical distance, they might not be part of the same title
    title_parts = []
    prev_y1 = None
    for s in title_spans_sorted:
        text = s["text"].strip()
        if not text:
            continue
        
        y0, y1 = s["bbox"][1], s["bbox"][3]
        if prev_y1 is not None:
            # If vertical distance between lines is larger than twice the font size, they might be different fields
            if y0 - prev_y1 > s["size"] * 2.2:
                # We stop gathering more lines once a large gap is hit, to avoid sucking in authors/affiliations
                break
        
        title_parts.append(text)
        prev_y1 = y1

    title = " ".join(title_parts)
    return clean_title(title)

def extract_title_heuristic(text: str) -> str:
    """
    Text-based title extraction heuristic when font size spans are unavailable.
    """
    if not text:
        return ""
    
    lines = text.split("\n")
    cleaned_lines = []
    
    # Filter lines
    for line in lines:
        line_clean = line.strip()
        if not line_clean:
            continue
        if len(line_clean) < 10:
            continue
        if is_boilerplate(line_clean):
            continue
        # Check if line looks like author list or abstract header
        if re.match(r'^(abstract|keywords|introduction|summary|isbn|issn)', line_clean, re.IGNORECASE):
            break  # Stop searching once we hit key section headers
        if re.search(r'(@|\bby\b|department|university|institute)', line_clean, re.IGNORECASE):
            continue
        cleaned_lines.append(line_clean)
        if len(cleaned_lines) >= 4:
            break

    if not cleaned_lines:
        return ""

    # Usually the first 1-2 lines after boilerplate form the title
    title_candidate = " ".join(cleaned_lines[:2])
    return clean_title(title_candidate)

def extract_title(reader: PDFReader) -> str:
    """
    Unified title extraction. First attempts span-based (font size) extraction,
    then falls back to heuristic text-based extraction.
    """
    # 1. Try PyMuPDF span-based extraction
    spans = reader.get_first_page_spans()
    title = extract_title_from_spans(spans)
    
    # 2. Fallback to heuristic text extraction if span-based extraction failed or yielded too short text
    if not title or len(title) < 8:
        first_page_text = reader.get_text(max_pages=1)
        title = extract_title_heuristic(first_page_text)
        
    return title
