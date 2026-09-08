import re
import html

def clean_html(text: str) -> str:
    """Removes HTML tags and decodes HTML entities."""
    if not text:
        return ""
    # Remove HTML tags
    clean = re.sub(r'<[^>]+>', ' ', text)
    # Decode HTML entities (e.g. &amp; -> &)
    clean = html.unescape(clean)
    return clean

def clean_transcript(text: str) -> str:
    """Removes WEBVTT headers, timestamps, and formatting from transcript."""
    if not text:
        return ""
    
    # Remove WEBVTT header
    text = text.replace("WEBVTT", "")
    
    # Remove timestamps like: 00:00:08.000 --> 00:00:021
    text = re.sub(r'\d{2}:\d{2}:\d{2}\.\d{3}\s*-->\s*\d{2}:\d{2}:\d{2,3}', '', text)
    
    # Extract speaker tags <v Name>Text</v> -> Name: Text
    text = re.sub(r'<v\s+([^>]+)>(.*?)</v>', r'\1: \2', text, flags=re.DOTALL)
    
    return text

def normalize_whitespace(text: str) -> str:
    """Removes extra spaces and empty lines."""
    if not text:
        return ""
    # Replace multiple spaces/newlines with a single space
    clean = re.sub(r'\s+', ' ', text)
    return clean.strip()

def clean_email_body(body: str) -> str:
    """Cleans email HTML body and normalizes it."""
    cleaned = clean_html(body)
    return normalize_whitespace(cleaned)

def clean_event_body(body: str) -> str:
    """Cleans calendar event HTML body and normalizes it."""
    cleaned = clean_html(body)
    return normalize_whitespace(cleaned)

def clean_meeting_transcript(transcript: str) -> str:
    """Cleans meeting transcript and normalizes it."""
    cleaned = clean_transcript(transcript)
    return normalize_whitespace(cleaned)
