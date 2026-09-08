import os
import json
import re
from datetime import datetime

def parse_wiki(file_path: str) -> dict:
    if not os.path.exists(file_path):
        return {"metadata": {}, "content": ""}
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    match = re.match(r"^---\n(.*?)\n---\n(.*)$", content, re.DOTALL)
    if match:
        meta_str = match.group(1)
        body = match.group(2).strip()
        metadata = {}
        for line in meta_str.split('\n'):
            if ':' in line:
                key, val = line.split(':', 1)
                try:
                    metadata[key.strip()] = json.loads(val.strip())
                except json.JSONDecodeError:
                    metadata[key.strip()] = val.strip()
        return {"metadata": metadata, "content": body}
    
    return {"metadata": {}, "content": content}

def save_wiki(file_path: str, wiki_data: dict):
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write("---\n")
        for k, v in wiki_data["metadata"].items():
            f.write(f"{k}: {json.dumps(v)}\n")
        f.write("---\n\n")
        f.write(wiki_data["content"])

def sanitize_filename(name: str) -> str:
    if not name:
        return "unknown"
    return re.sub(r'[^\w\s-]', '', name).strip().replace(' ', '_').lower()

def update_list(metadata: dict, key: str, item):
    if key not in metadata:
        metadata[key] = []
    if item and item not in metadata[key]:
        metadata[key].append(item)

def generate_wikis(events: list[dict], base_dir: str):
    wiki_dir = os.path.join(base_dir, "Wikis")
    dirs = {
        "Salespersons": os.path.join(wiki_dir, "Salespersons"),
        "Customers": os.path.join(wiki_dir, "Customers"),
        "Projects": os.path.join(wiki_dir, "Projects"),
        "People": os.path.join(wiki_dir, "People"),
        "Events": os.path.join(wiki_dir, "Events")
    }
    
    for d in dirs.values():
        os.makedirs(d, exist_ok=True)
        
    for event in events:
        event_id = event.get("source_id", "unknown_event")
        evt_type = event.get("event_type", "unknown")
        sp = event.get("salesperson")
        cust = event.get("customer")
        proj = event.get("project")
        participants = event.get("participants", [])
        
        # Event Wiki
        evt_path = os.path.join(dirs["Events"], f"{event_id}.md")
        evt_wiki = parse_wiki(evt_path)
        evt_wiki["metadata"]["id"] = event_id
        evt_wiki["metadata"]["type"] = evt_type
        evt_wiki["metadata"]["project"] = proj
        evt_wiki["metadata"]["customer"] = cust
        evt_wiki["metadata"]["salesperson"] = sp
        evt_wiki["content"] = event.get("summary", "")
        save_wiki(evt_path, evt_wiki)
        
        # Salesperson Wiki
        if sp:
            sp_path = os.path.join(dirs["Salespersons"], f"{sanitize_filename(sp)}.md")
            sp_wiki = parse_wiki(sp_path)
            sp_wiki["metadata"]["name"] = sp
            update_list(sp_wiki["metadata"], "customers", cust)
            update_list(sp_wiki["metadata"], "projects", proj)
            if not sp_wiki["content"]:
                sp_wiki["content"] = f"# Salesperson: {sp}\n"
            save_wiki(sp_path, sp_wiki)
            
        # Customer Wiki
        if cust:
            cust_path = os.path.join(dirs["Customers"], f"{sanitize_filename(cust)}.md")
            cust_wiki = parse_wiki(cust_path)
            cust_wiki["metadata"]["name"] = cust
            update_list(cust_wiki["metadata"], "projects", proj)
            if not cust_wiki["content"]:
                cust_wiki["content"] = f"# Customer: {cust}\n"
            save_wiki(cust_path, cust_wiki)
            
        # Project Wiki
        if proj:
            proj_path = os.path.join(dirs["Projects"], f"{sanitize_filename(proj)}.md")
            proj_wiki = parse_wiki(proj_path)
            proj_wiki["metadata"]["name"] = proj
            proj_wiki["metadata"]["status"] = proj_wiki["metadata"].get("status", "Active")
            proj_wiki["metadata"]["latest_update"] = datetime.now().isoformat()
            proj_wiki["metadata"]["created_at"] = proj_wiki["metadata"].get("created_at", datetime.now().isoformat())
            update_list(proj_wiki["metadata"], "customers", cust)
            update_list(proj_wiki["metadata"], "salespersons", sp)
            
            if evt_type == "meeting":
                update_list(proj_wiki["metadata"], "meetings", event_id)
            elif evt_type == "mail":
                update_list(proj_wiki["metadata"], "emails", event_id)
            elif evt_type == "calendar_event":
                update_list(proj_wiki["metadata"], "calendar_events", event_id)
                
            for p in participants:
                update_list(proj_wiki["metadata"], "participants", p.get("email", p.get("name")))
                
            if not proj_wiki["content"]:
                proj_wiki["content"] = f"# Project: {proj}\n"
            save_wiki(proj_path, proj_wiki)
            
        # People Wiki
        for p in participants:
            name = p.get("name")
            email = p.get("email")
            if name or email:
                person_id = email if email else name
                person_path = os.path.join(dirs["People"], f"{sanitize_filename(person_id)}.md")
                person_wiki = parse_wiki(person_path)
                person_wiki["metadata"]["name"] = name
                person_wiki["metadata"]["email"] = email
                update_list(person_wiki["metadata"], "customers", cust)
                update_list(person_wiki["metadata"], "projects", proj)
                if not person_wiki["content"]:
                    person_wiki["content"] = f"# Person: {name or email}\n"
                save_wiki(person_path, person_wiki)
