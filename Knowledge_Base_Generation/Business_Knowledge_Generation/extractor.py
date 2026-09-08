import json
import os
from cleaner import clean_email_body, clean_event_body, clean_meeting_transcript

def load_json(filepath: str) -> dict | list:
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def extract_emails(filepath: str) -> list[dict]:
    data = load_json(filepath)
    if isinstance(data, dict) and "value" in data:
        items = data["value"]
    else:
        items = data if isinstance(data, list) else [data]
        
    extracted = []
    for item in items:
        # Some graphs wrap emails in `resourceData` or `message`
        msg = item.get("message", item)
        
        body_content = ""
        if "body" in msg and isinstance(msg["body"], dict):
            body_content = msg["body"].get("content", "")
            
        cleaned_body = clean_email_body(body_content)
        
        participants = []
        if "from" in msg and "emailAddress" in msg["from"]:
            participants.append(msg["from"]["emailAddress"])
        for recipient in msg.get("toRecipients", []):
            if "emailAddress" in recipient:
                participants.append(recipient["emailAddress"])
        
        extracted.append({
            "source_id": msg.get("id"),
            "event_type": "mail",
            "subject": msg.get("subject", ""),
            "date": msg.get("receivedDateTime") or msg.get("sentDateTime", ""),
            "participants": participants,
            "raw_content": body_content,
            "cleaned_data": cleaned_body
        })
        
    return extracted

def extract_calendar_events(filepath: str) -> list[dict]:
    data = load_json(filepath)
    if isinstance(data, dict) and "value" in data:
        items = data["value"]
    else:
        items = data if isinstance(data, list) else [data]
        
    extracted = []
    for item in items:
        body_content = ""
        if "body" in item and isinstance(item["body"], dict):
            body_content = item["body"].get("content", "")
            
        cleaned_body = clean_event_body(body_content)
        
        participants = []
        if "organizer" in item and "emailAddress" in item["organizer"]:
            participants.append(item["organizer"]["emailAddress"])
            
        for attendee in item.get("attendees", []):
            if "emailAddress" in attendee:
                participants.append(attendee["emailAddress"])
                
        extracted.append({
            "source_id": item.get("id"),
            "event_type": "calendar_event",
            "subject": item.get("subject", ""),
            "date": item.get("start", {}).get("dateTime", ""),
            "participants": participants,
            "raw_content": body_content,
            "cleaned_data": cleaned_body
        })
        
    return extracted

def extract_transcripts(filepath: str) -> list[dict]:
    data = load_json(filepath)
    if isinstance(data, dict) and "value" in data:
        items = data["value"]
    else:
        items = data if isinstance(data, list) else [data]
        
    extracted = []
    for item in items:
        transcript_content = item.get("content", "")
        cleaned_transcript = clean_meeting_transcript(transcript_content)
        
        participants = item.get("participants", [])
        # Add organizer if not in participants
        if "meetingOrganizer" in item and "user" in item["meetingOrganizer"]:
            org_user = item["meetingOrganizer"]["user"]
            org_email = org_user.get("userPrincipalName", org_user.get("id", "")) # ID is used as fallback
            participants.append({"name": org_user.get("displayName", ""), "address": org_email})
            
        metadata = item.get("salesContext", {})
        
        extracted.append({
            "source_id": item.get("id"),
            "event_type": "meeting",
            "subject": f"Meeting regarding {metadata.get('projectName', 'Unknown')} with {metadata.get('customerName', 'Unknown')}",
            "date": item.get("createdDateTime", ""),
            "participants": participants,
            "metadata": metadata,
            "raw_content": transcript_content,
            "cleaned_data": cleaned_transcript
        })
        
    return extracted

def extract_all_datasets(datasets_dir: str) -> list[dict]:
    all_events = []
    
    calendar_path = os.path.join(datasets_dir, "data_calendar_event.json")
    if os.path.exists(calendar_path):
        all_events.extend(extract_calendar_events(calendar_path))
        
    emails_path = os.path.join(datasets_dir, "data_emails.json")
    if os.path.exists(emails_path):
        all_events.extend(extract_emails(emails_path))
        
    meets_path = os.path.join(datasets_dir, "data_meets.json")
    if os.path.exists(meets_path):
        all_events.extend(extract_transcripts(meets_path))
        
    return all_events
