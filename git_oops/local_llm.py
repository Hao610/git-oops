"""
Git-Oops Pure-Offline Local LLM Adapter
Connects directly to local Ollama (http://localhost:11434) or vLLM / LM Studio (http://localhost:8000).
100% offline, zero data exfiltration, zero token cost, zero external Python dependencies.
"""

import os
import sys
import json
import urllib.request
import urllib.error
from typing import Tuple, Dict, Any, Optional

DEFAULT_OLLAMA_URL = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
DEFAULT_VLLM_URL = os.environ.get("VLLM_HOST", "http://localhost:8000")


def probe_local_llm(timeout: float = 0.35) -> Tuple[bool, str, str]:
    """
    Sub-second probe to detect running local LLM daemon.
    Returns: (is_available: bool, provider_name: str, detected_model: str)
    """
    # 1. Probe Ollama
    try:
        req = urllib.request.Request(f"{DEFAULT_OLLAMA_URL}/api/tags")
        with urllib.request.urlopen(req, timeout=timeout) as res:
            if res.status == 200:
                data = json.loads(res.read().decode("utf-8"))
                models = data.get("models", [])
                chosen_model = models[0]["name"] if models else "llama3"
                return True, "Ollama", chosen_model
    except Exception:
        pass

    # 2. Probe vLLM / OpenAI-compatible local server
    try:
        req = urllib.request.Request(f"{DEFAULT_VLLM_URL}/v1/models")
        with urllib.request.urlopen(req, timeout=timeout) as res:
            if res.status == 200:
                data = json.loads(res.read().decode("utf-8"))
                models = data.get("data", [])
                chosen_model = models[0]["id"] if models else "default"
                return True, "vLLM", chosen_model
    except Exception:
        pass

    return False, "None", "none"


def call_local_llm(
    prompt: str,
    system_prompt: str = "You are a senior systems engineer repairing code crashes.",
    model: Optional[str] = None,
    timeout: float = 30.0
) -> Tuple[bool, str]:
    """
    Invokes local LLM to produce code fix or diagnostic analysis.
    Returns: (success: bool, response_text: str)
    """
    avail, provider, detected_model = probe_local_llm()
    if not avail:
        return False, "No local LLM daemon detected. Please ensure Ollama or vLLM is running locally."

    active_model = model or detected_model

    if provider == "Ollama":
        url = f"{DEFAULT_OLLAMA_URL}/api/chat"
        payload = {
            "model": active_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            "stream": False,
            "options": {"temperature": 0.1}
        }
        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=timeout) as res:
                if res.status == 200:
                    resp_json = json.loads(res.read().decode("utf-8"))
                    content = resp_json.get("message", {}).get("content", "")
                    return True, content
        except Exception as e:
            return False, f"Ollama local inference failed: {str(e)}"

    elif provider == "vLLM":
        url = f"{DEFAULT_VLLM_URL}/v1/chat/completions"
        payload = {
            "model": active_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.1
        }
        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=timeout) as res:
                if res.status == 200:
                    resp_json = json.loads(res.read().decode("utf-8"))
                    choices = resp_json.get("choices", [])
                    content = choices[0]["message"]["content"] if choices else ""
                    return True, content
        except Exception as e:
            return False, f"vLLM local inference failed: {str(e)}"

    return False, "Unsupported local LLM provider."
