import os
import sys
import shutil

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from extractor import extract_all_datasets
from agent_workflow import process_event
from data_layer import save_structured_data
from wiki_generator import generate_wikis
from kg_generator import generate_knowledge_graph

def main():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    knowledge_bases_dir = os.path.join(base_dir, "Knowledge_Bases", "Business")
    datasets_dir = os.path.join(base_dir, "datasets")
    
    print(f"Checking for existing Business Knowledge Base at: {knowledge_bases_dir}")
    if os.path.exists(knowledge_bases_dir):
        print("Found existing Knowledge Base. Deleting it completely...")
        shutil.rmtree(knowledge_bases_dir)
        
    print("Creating fresh Business Knowledge Base structure...")
    os.makedirs(knowledge_bases_dir, exist_ok=True)
    
    print(f"Processing datasets from: {datasets_dir}")
    raw_events = extract_all_datasets(datasets_dir)
    print(f"Extracted {len(raw_events)} raw events.")
    
    normalized_events = []
    for i, event in enumerate(raw_events):
        print(f"Normalizing event {i+1}/{len(raw_events)} (ID: {event.get('source_id')})...")
        normalized = process_event(event)
        normalized_events.append(normalized)
        
    print(f"Saving structured data to {knowledge_bases_dir}...")
    save_structured_data(normalized_events, knowledge_bases_dir)
    
    print(f"Generating OKF Wikis at {knowledge_bases_dir}...")
    generate_wikis(normalized_events, knowledge_bases_dir)
    
    print(f"Generating Knowledge Graph at {knowledge_bases_dir}...")
    generate_knowledge_graph(normalized_events, knowledge_bases_dir)
    
    print("Business Knowledge Generation completed successfully.")

if __name__ == "__main__":
    main()
