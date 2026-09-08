import os
import json

def save_structured_data(normalized_events: list[dict], base_dir: str):
    """Saves structured data to a JSONL file in the local data layer."""
    output_dir = os.path.join(base_dir, "Structured_Data")
    os.makedirs(output_dir, exist_ok=True)
    
    file_path = os.path.join(output_dir, "structured_data.jsonl")
    
    with open(file_path, 'w', encoding='utf-8') as f:
        for event in normalized_events:
            f.write(json.dumps(event) + "\n")
            
    print(f"Saved {len(normalized_events)} normalized events to {file_path}")

def load_structured_data(base_dir: str) -> list[dict]:
    """Loads structured data from the local data layer."""
    file_path = os.path.join(base_dir, "Structured_Data", "structured_data.jsonl")
    events = []
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    events.append(json.loads(line))
    return events
