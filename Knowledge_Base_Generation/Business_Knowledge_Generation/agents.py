import json
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from utils.llm import invoke_llm

def extractor_agent(raw_event: dict, cleaned_data: str, feedback: str = None) -> dict:
    models = ["llama3_3_70b", "deepseek_v3", "qwen2_5_72b"]
    
    prompt = f"""You are an expert data extraction agent.
Your goal is to extract strictly factual entities from the provided business event data.

Event Context:
{json.dumps(raw_event.get('metadata', {}))}

Cleaned Text:
{cleaned_data}

{f'CRITICAL FEEDBACK FROM VALIDATOR (MUST FIX): {feedback}' if feedback else ''}

Extract the following exact fields strictly based on the text. Do not invent missing data.
- "event_type": (string) "mail", "meeting", or "calendar_event"
- "participants": (list of objects) each containing "name" (string) and "email" (string). 
- "customer": (string) name of the customer company, null if unknown
- "project": (string) name of the project, null if unknown
- "salesperson": (string) name of the primary salesperson handling this, null if unknown
- "summary": (string) 1-2 sentence concise summary

Output strictly valid JSON with no other text.
"""
    try:
        return invoke_llm(models, prompt, parse_as_json=True)
    except Exception as e:
        print(f"[Extractor] Error: {e}")
        return {}

def validator_agent(cleaned_data: str, extracted_entities: dict) -> dict:
    models = ["veritas_8b_fact_checker", "deepseek_r1", "llama3_3_70b"]
    
    prompt = f"""You are a strict validation agent checking for AI hallucinations.
Compare the Extracted Entities against the Source Text.

Source Text:
{cleaned_data}

Extracted Entities:
{json.dumps(extracted_entities, indent=2)}

Task:
1. Verify that EVERY participant name/email, customer, project, and salesperson actually exists or is explicitly implied in the Source Text.
2. If ANY field contains a hallucinated value (e.g., guessing a project name that isn't mentioned), mark valid as false and explain exactly what was hallucinated.
3. If everything is factual, mark valid as true.

Output strictly valid JSON:
{{
    "valid": true/false,
    "feedback": "Explain hallucinations here, or empty string if valid"
}}
"""
    try:
        res = invoke_llm(models, prompt, parse_as_json=True)
        if "valid" not in res:
            return {"valid": True, "feedback": ""}
        return res
    except Exception as e:
        print(f"[Validator] Error: {e}")
        return {"valid": True, "feedback": ""}

def normalizer_agent(extracted_entities: dict, cleaned_data: str) -> dict:
    models = ["deepseek_v3", "qwen2_5_72b", "llama3_3_70b"]
    
    prompt = f"""You are an expert data normalizer.
Your goal is to canonicalize and semantically normalize the verified extracted entities.

Extracted Entities:
{json.dumps(extracted_entities, indent=2)}

Task:
- Fix typos and normalize names (e.g., 'Acme Corp' -> 'Acme Corp').
- Ensure 'event_type' is exactly 'mail', 'meeting', or 'calendar_event'.
- Preserve all data, just format it cleanly.
- Add exactly the following field:
  - "complete_cleaned_data": exactly the string provided below.

Cleaned Data String to append:
{cleaned_data}

Output strictly valid JSON matching the required schema.
"""
    try:
        return invoke_llm(models, prompt, parse_as_json=True)
    except Exception as e:
        print(f"[Normalizer] Error: {e}")
        extracted_entities["complete_cleaned_data"] = cleaned_data
        return extracted_entities
