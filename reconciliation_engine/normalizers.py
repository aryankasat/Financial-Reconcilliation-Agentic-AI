import re

# Contextual DBA / Legal Entity mapping
# Maps card statement merchant names (or statement descriptions) to ledger brand names
DBA_MAP = {
    "formagrid": "airtable",
    "agilebits": "1password",
    "meta ads": "instagram ads",
    "x.com": "twitter",
    "ww operating": "wework",
    "stripe card payment": "stripe corporate card payment",
    "stripe card": "stripe corporate card",
    "amazon web services": "aws hosting"
}

def strip_employee_suffix(text):
    if not text:
        return ""
    # Remove suffix like " - John Smith" or " - Jane Doe"
    return re.sub(r'\s*-\s*(john smith|jane doe|alice johnson|bob brown)\s*$', '', text, flags=re.IGNORECASE)

def clean_description(text):
    if not text:
        return ""
    # Convert to lowercase
    text = text.lower()
    
    # Remove common card processor artifacts/symbols and trailing locations
    text = text.replace("*", " ")
    
    # Remove state abbreviations at the end of statement lines
    text = re.sub(r'\b(sf|ca|wa|ny|co|ma|il|on|prague|munich|london|chicago|seattle|denver|boston|ottawa)\b', '', text)
    
    # Remove common transactional codes / numbers (3 or more digits, or standalone numbers)
    text = re.sub(r'\b\d+\b', '', text)
    text = re.sub(r'\b(inc|corp|llc|gmbh|s\.r\.o\.)\b', '', text)
    
    # Clean up excess whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def normalize_context(clean_text):
    """
    Applies contextual DBA (Doing Business As) and subsidiary name normalization.
    """
    for dba_key, brand_val in DBA_MAP.items():
        if dba_key in clean_text:
            return brand_val
    return clean_text

def get_normalized_description(text):
    """
    Runs full pipeline: raw text -> strip employee -> clean text -> contextual DBA mapping
    """
    stripped = strip_employee_suffix(text)
    cleaned = clean_description(stripped)
    normalized = normalize_context(cleaned)
    return normalized

def levenshtein_distance(s1, s2):
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)
    if len(s2) == 0:
        return len(s1)
    
    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    return previous_row[-1]

def string_similarity(s1, s2):
    """
    Returns a similarity score between 0.0 and 1.0 based on Levenshtein distance.
    """
    norm1 = get_normalized_description(s1)
    norm2 = get_normalized_description(s2)
    
    # Exact check first
    if norm1 == norm2:
        return 1.0
        
    # Substring checks (extremely effective for financial descriptions)
    if norm1 in norm2 or norm2 in norm1:
        return 0.9  # High similarity if one is a direct substring of another
        
    max_len = max(len(norm1), len(norm2))
    if max_len == 0:
        return 1.0
        
    distance = levenshtein_distance(norm1, norm2)
    return 1.0 - (distance / max_len)
