import os
import time
from dotenv import load_dotenv
from langchain_community.llms import Ollama

from utils.parser import clean_text, extract_json

load_dotenv()

llm_client = None

def start_connection():
    global llm_client
    print("[Ollama] Pre-initializing connection to deepseek-r1:8b...")
    llm_client = Ollama(
        model="deepseek-r1:8b",
        temperature=0.6,
        keep_alive=-1
    )

def invoke_llm(model_names: list[str], prompt: str, parse_as_json: bool = False):
    global llm_client
    
    if llm_client is None:
        raise RuntimeError("LLM client is not initialized. Call start_connection() first.")
        
    target_model = "deepseek-r1:8b"
    retries = 0
    
    while retries < 3:
        try:
            response = llm_client.invoke(prompt)
            
            if parse_as_json:
                return extract_json(response)
            else:
                return clean_text(response)
                
        except Exception as e:
            print(f"[Ollama] Error calling {target_model}: {e}")
            retries += 1
            if retries < 3:
                time.sleep(2 ** retries)
            else:
                raise RuntimeError(f"All retries failed for Ollama model {target_model}. Error: {e}")