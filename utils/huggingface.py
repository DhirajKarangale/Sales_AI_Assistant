import os
import json
import time
from dotenv import load_dotenv
from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint

from utils.parser import clean_text, extract_json

load_dotenv()

BASE_DIR = os.path.dirname(__file__)
JSON_PATH = os.path.join(BASE_DIR, "LLMs.json")

with open(JSON_PATH, "r") as file:
    LLMs = json.load(file)

hf_tokens_env = os.getenv("HF_TOKENS")
if not hf_tokens_env or not hf_tokens_env.strip():
    raise ValueError("Missing required environment variable: HF_TOKENS")

HF_TOKENS = [t.strip() for t in hf_tokens_env.split(",") if t.strip()]
if not HF_TOKENS:
    raise ValueError("HF_TOKENS environment variable contains no valid tokens.")

class AllTokensExhaustedException(Exception):
    """Raised when all HuggingFace API tokens provided in HF_TOKENS environment variable are exhausted or rate-limited."""
    pass


_current_token_index = 0
_exhausted_token_indices = set()
_connected_llms = {}


def _get_llm(name: str, token_index: int):
    if token_index not in _connected_llms:
        _connected_llms[token_index] = {}

    if name in _connected_llms[token_index]:
        return _connected_llms[token_index][name]

    cfg = next((item for item in LLMs if item["name"] == name), None)
    if not cfg:
        raise ValueError(f"LLM '{name}' not found in LLMs.json.")

    token = HF_TOKENS[token_index]

    provider = cfg.get("provider")
    if provider in ["auto", "huggingface", ""]:
        provider = None

    endpoint_kwargs = {
        "task": cfg["task"],
        "repo_id": cfg["model_id"],
        "do_sample": cfg.get("do_sample", False),
        "temperature": cfg.get("temperature", 0.1),
        "max_new_tokens": max(cfg.get("max_new_tokens", 512), 1024),
        "repetition_penalty": cfg.get("repetition_penalty", 1.03),
        "return_full_text": False,
        "huggingfacehub_api_token": token,
    }
    if provider:
        endpoint_kwargs["provider"] = provider

    endpoint = HuggingFaceEndpoint(**endpoint_kwargs)

    if cfg["task"] == "conversational":
        llm = ChatHuggingFace(llm=endpoint)
    else:
        llm = endpoint

    _connected_llms[token_index][name] = llm
    return llm


def invoke_llm(model_names: list[str], prompt: str, parse_as_json: bool = False):
    global _current_token_index, _exhausted_token_indices

    if len(_exhausted_token_indices) >= len(HF_TOKENS):
        raise AllTokensExhaustedException(
            f"All {len(HF_TOKENS)} HuggingFace API token(s) from environment variables are exhausted or rate-limited."
        )

    for model_name in model_names:
        attempts_with_different_tokens = 0

        while attempts_with_different_tokens < len(HF_TOKENS):
            if len(_exhausted_token_indices) >= len(HF_TOKENS):
                raise AllTokensExhaustedException(
                    f"All {len(HF_TOKENS)} HuggingFace API token(s) from environment variables are exhausted or rate-limited."
                )

            network_retries = 0

            while network_retries < 3:
                try:
                    llm = _get_llm(model_name, _current_token_index)
                    response = llm.invoke(prompt)
                    if parse_as_json:
                        return extract_json(response)
                    else:
                        return clean_text(response)

                except Exception as e:
                    error_msg = str(e).lower()
                    limit_keywords = [
                        "rate limit",
                        "quota",
                        "upgrade",
                        "429",
                        "too many requests",
                        "402",
                        "payment required",
                        "depleted",
                        "credits",
                        "exceeded",
                        "forbidden",
                        "unauthorized",
                    ]

                    if any(keyword in error_msg for keyword in limit_keywords):
                        _exhausted_token_indices.add(_current_token_index)
                        print(
                            f"[HuggingFace] Rate limit/Quota hit on token index {_current_token_index} "
                            f"({len(_exhausted_token_indices)}/{len(HF_TOKENS)} tokens exhausted)."
                        )
                        _current_token_index = (_current_token_index + 1) % len(HF_TOKENS)
                        attempts_with_different_tokens += 1
                        if len(_exhausted_token_indices) >= len(HF_TOKENS):
                            raise AllTokensExhaustedException(
                                f"All {len(HF_TOKENS)} HuggingFace API token(s) from environment variables are exhausted or rate-limited."
                            )
                        break
                    else:
                        network_retries += 1
                        if network_retries < 3:
                            delay = 2 ** network_retries
                            time.sleep(delay)
                        else:
                            attempts_with_different_tokens += 1
                            break

    if len(_exhausted_token_indices) >= len(HF_TOKENS):
        raise AllTokensExhaustedException(
            f"All {len(HF_TOKENS)} HuggingFace API token(s) from environment variables are exhausted or rate-limited."
        )

    raise RuntimeError("All models and tokens failed to generate a valid response.")

