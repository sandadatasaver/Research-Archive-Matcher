import re

ABSTRACT_START_RE = re.compile(r'\b(abstract|summary|executive summary)\b[:.\-\s]', re.IGNORECASE)
ABSTRACT_END_RE = re.compile(r'\b(introduction|key\s*words|keywords|background|materials|methods|1\s*\.\s*introduction|1\s*introduction)\b', re.IGNORECASE)

def extract_abstract(text: str) -> str:
    """
    Extracts the abstract/summary from the PDF text.
    Searches for 'Abstract' or 'Summary' on the first pages, extracts following text,
    and cuts off when an introduction or keywords section begins.
    """
    if not text:
        return ""
        
    # Search for abstract starting position
    match = ABSTRACT_START_RE.search(text)
    if not match:
        # If no explicit "Abstract" keyword, let's look for text between authors and Introduction
        # but that can be risky, so we only do it if we find "Introduction"
        intro_match = re.search(r'\b(1\s*\.\s*introduction|1\s*introduction|introduction)\b', text, re.IGNORECASE)
        if intro_match and intro_match.start() > 100:
            # Maybe abstract is the block right before introduction?
            # Let's take up to 1000 chars before introduction
            candidate = text[max(0, intro_match.start() - 1000):intro_match.start()].strip()
            # Try to grab the last paragraph block
            blocks = candidate.split('\n\n')
            if len(blocks) > 1:
                return blocks[-1].strip()
            return ""
        return ""

    start_idx = match.end()
    remaining_text = text[start_idx:].strip()
    
    # Find ending delimiter
    end_match = ABSTRACT_END_RE.search(remaining_text)
    if end_match:
        abstract_body = remaining_text[:end_match.start()].strip()
    else:
        # Fallback: take first 1500 characters
        abstract_body = remaining_text[:1500].strip()
        # Clean up to the last complete sentence
        last_dot = abstract_body.rfind('.')
        if last_dot != -1 and last_dot > 200:
            abstract_body = abstract_body[:last_dot + 1]

    # Clean up multi-lines/whitespace
    abstract_body = re.sub(r'\s+', ' ', abstract_body)
    return abstract_body
