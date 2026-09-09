import re
import html

def clean_html(text: str) -> str:
    if not text:
        return ""
    clean = re.sub(r'<[^>]+>', ' ', text)
    clean = html.unescape(clean)
    return clean

def clean_transcript(text: str) -> str:
    if not text:
        return ""
    
    text = text.replace("WEBVTT", "")
    text = re.sub(r'\d{2}:\d{2}:\d{2}\.\d{3}\s*-->\s*\d{2}:\d{2}:\d{2,3}', '', text)
    text = re.sub(r'<v\s+([^>]+)>(.*?)</v>', r'\1: \2', text, flags=re.DOTALL)
    
    return text

def normalize_whitespace(text: str) -> str:
    if not text:
        return ""
    clean = re.sub(r'\s+', ' ', text)
    return clean.strip()

def clean_email_body(body: str) -> str:
    cleaned = clean_html(body)
    return normalize_whitespace(cleaned)

def clean_event_body(body: str) -> str:
    cleaned = clean_html(body)
    return normalize_whitespace(cleaned)

def clean_meeting_transcript(transcript: str) -> str:
    cleaned = clean_transcript(transcript)
    return normalize_whitespace(cleaned)
