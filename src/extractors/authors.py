import re

AFFILIATION_KEYWORDS = [
    r'university', r'department', r'institute', r'school', r'academy', r'laboratory', r'center',
    r'centre', r'hospital', r'college', r'clinic', r'division', r'faculty', r'state key', r'corporation',
    r'inc\.', r'ltd\.', r'llc', r'gmbh', r'co\.', r'author for correspondence', r'email:', r'@'
]

AFFILIATION_RE = re.compile(r'\b(' + '|'.join(AFFILIATION_KEYWORDS) + r')\b', re.IGNORECASE)

# Name components regex: capitalized words, optional middle initials, sometimes hyphenated
# Excluding common keywords
NAME_RE = re.compile(r'\b[A-Z][a-z]+(?:\s+[A-Z]\.?)*(?:\s+[A-Z][a-z]+)+\b')

def clean_author_name(name: str) -> str:
    """
    Cleans up an author name string by removing superscripts, symbols, and excess spaces.
    """
    # Remove digits and common superscript symbols (e.g. *, 1, 2, a, b, c, †)
    cleaned = re.sub(r'[\d*†‡§|]+', '', name)
    cleaned = cleaned.strip()
    
    # Remove trailing/leading punctuation
    cleaned = cleaned.strip(',;. \t')
    
    # Normalize internal whitespace
    cleaned = re.sub(r'\s+', ' ', cleaned)
    return cleaned

def extract_authors(first_page_text: str, title: str, abstract_text: str = "") -> str:
    """
    Extracts author names from the first page text.
    Uses the context between the Title and the Abstract/Introduction if possible.
    """
    if not first_page_text:
        return ""
    
    lines = [line.strip() for line in first_page_text.split('\n') if line.strip()]
    
    # Try to locate title index and abstract/introduction index
    title_idx = -1
    abstract_idx = -1
    
    # Find index of line that contains or matches the title
    if title:
        title_words = [w for w in re.findall(r'\w+', title.lower()) if len(w) > 3]
        for i, line in enumerate(lines):
            line_lower = line.lower()
            # If we find a line with high overlap with the title, or containing it
            if title.lower() in line_lower or (title_words and sum(1 for w in title_words if w in line_lower) >= max(1, len(title_words) // 2)):
                title_idx = i
                break
                
    # Find index of line that looks like abstract or introduction
    for i, line in enumerate(lines):
        line_lower = line.lower()
        if i > title_idx and (line_lower.startswith('abstract') or line_lower.startswith('summary') or line_lower.startswith('introduction')):
            abstract_idx = i
            break
            
    # Default search range if title/abstract not clearly found
    start_search = title_idx + 1 if title_idx != -1 else 1
    end_search = abstract_idx if abstract_idx != -1 else min(len(lines), start_search + 15)
    
    author_lines = []
    for i in range(start_search, end_search):
        line = lines[i]
        # Skip if it is obviously affiliation, email, or boilerplate
        if AFFILIATION_RE.search(line):
            continue
        # Also avoid duplicating title words if title_idx was wrong
        if title and sum(1 for w in re.findall(r'\w+', line.lower()) if len(w) > 3 and w in title.lower()) > 3:
            continue
        author_lines.append(line)
        
    # Join candidates
    joined_text = " ".join(author_lines)
    
    # Split by common separators: comma, and, &, or semicolon
    # But preserve hyphens in last names (like Smith-Jones)
    parts = re.split(r'[,;&]|\band\b', joined_text)
    
    authors = []
    for part in parts:
        part_clean = clean_author_name(part)
        # Ensure it looks like a person's name (at least 2 words, capitalized, reasonable length)
        if len(part_clean) > 3 and len(part_clean) < 40:
            words = part_clean.split()
            if len(words) >= 2 and all(w[0].isupper() or w[0] in ['v', 'd'] for w in words if w):
                authors.append(part_clean)
                
    # If the smart heuristic fails, find capitalized name patterns in the text
    if not authors:
        # Search the first page for likely name patterns
        search_chunk = " ".join(lines[start_search:end_search])
        candidates = NAME_RE.findall(search_chunk)
        for c in candidates:
            c_clean = clean_author_name(c)
            if c_clean and c_clean not in authors and not AFFILIATION_RE.search(c_clean):
                authors.append(c_clean)
                
    return ", ".join(authors[:8])  # Return top 8 authors
