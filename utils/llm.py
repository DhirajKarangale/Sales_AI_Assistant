import os
from dotenv import load_dotenv

from utils.huggingface import invoke_llm as hf_invoke_llm
from utils.ollama import invoke_llm as ollama_invoke_llm

load_dotenv()

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "huggingface").lower()

def invoke_llm(model_names: list[str], prompt: str, parse_as_json: bool = False):
    if LLM_PROVIDER == "huggingface":
        return hf_invoke_llm(model_names, prompt, parse_as_json)
        
    elif LLM_PROVIDER == "ollama":
        return ollama_invoke_llm(model_names, prompt, parse_as_json)
        
    else:
        raise ValueError(f"Unknown LLM_PROVIDER: {LLM_PROVIDER}. Please use 'ollama' or 'huggingface'.")
