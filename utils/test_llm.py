import os
import logging
from dotenv import load_dotenv
load_dotenv()
logging.basicConfig(level=logging.INFO)

from utils.huggingface import invoke_llm

def main():
    prompt = 'who is founder of google'
    ELIGIBILITY_MODELS = [
    "qwen2_5",
    "llama3_3_70b",
    "deepseek_v3",
    "deepseek_r1_distill_llama_8b",
    "hermes",
    "llama3",
    "mistral",
    "qwen2_5_7b",
    "phi3_mini",
    "gemma_7b",
    "zephyr",
]
   
    try:
        response = invoke_llm(
            ELIGIBILITY_MODELS,
            prompt
        )
        
        print("\n--- SUCCESS ---")
        print("Response:\n")
        print(response)
        print("\n----------------")
        
    except Exception as e:
        print("\n--- FAILED ---")
        print(f"Error during LLM invocation: {e}")

if __name__ == "__main__":
    main()
