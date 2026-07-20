from rapidfuzz import fuzz

def clean_string(s: str) -> str:
    """
    Normalizes string by lowercasing, stripping, and reducing whitespaces.
    """
    if not s:
        return ""
    import re
    return re.sub(r'\s+', ' ', s.lower().strip())

def compute_similarity(str1: str, str2: str) -> float:
    """
    Computes a robust similarity score between two strings using rapidfuzz.
    Combines direct ratio and token set ratio to handle phrasing variations.
    """
    s1 = clean_string(str1)
    s2 = clean_string(str2)
    
    if not s1 or not s2:
        return 0.0
        
    # Standard edit distance ratio
    ratio = fuzz.ratio(s1, s2)
    # Handles word reordering, insertion, deletion (perfect for citation vs clean title)
    token_set = fuzz.token_set_ratio(s1, s2)
    # Sorts words then calculates ratio
    token_sort = fuzz.token_sort_ratio(s1, s2)
    
    # We take a weighted average. Token set ratio is highly indicative for partial/unordered matches.
    # If the strings are almost identical, ratio will be very high.
    # Let's return a combination.
    score = (token_set * 0.5) + (token_sort * 0.3) + (ratio * 0.2)
    return float(score)

def is_match(str1: str, str2: str, threshold: float = 75.0) -> bool:
    """
    Returns True if the similarity score is above the threshold.
    """
    return compute_similarity(str1, str2) >= threshold
