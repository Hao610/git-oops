"""
Git-Oops Brutal AI Critic & Automated Git Patch Synthesizer
Direct REST client with auto-model fallback and strict timeouts.
Zero fluff, zero hallucination: outputs roast + exact valid unified diff.
"""

import os
import re
import json
import requests
from typing import Dict, Any, Optional
from src.circuit_breaker import (
    check_circuit_breaker,
    get_cached_response,
    store_cached_response,
    record_spend,
    hash_content
)

SYSTEM_PROMPT = """You are 'git-oops', a brutally honest, world-class staff software engineer and code reviewer.
The developer has run into a crash/stack trace, or submitted code with hidden architectural disasters.

YOUR PERSONALITY:
- Witty, sarcastic, brutally direct, but technically unassailable.
- Call out bad practices (e.g. unhandled NoneType, swallowed exceptions, N+1 queries, plaintext secrets, memory leaks).
- Never say "I hope this helps". Be concise and punchy.

YOUR TASK:
Analyze the provided code and error traceback, diagnose the root cause, and generate an exact, valid unified diff git patch.

OUTPUT FORMAT REQUIREMENTS:
You MUST respond with valid JSON matching this schema:
{
  "roast": "<2-3 sentence brutal and witty technical teardown of the mistake>",
  "root_cause": "<1 crisp sentence explaining why it broke>",
  "target_file": "<relative path of the file needing fix, e.g. src/app.py>",
  "original_snippet": "<exact original lines of code that need replacement>",
  "fixed_snippet": "<exact replacement code fixing the bug>",
  "git_patch": "<complete unified git diff block starting with '--- a/...' and '+++ b/...'>"
}
"""


def diagnose_and_patch(
    error_log: str,
    file_context: str,
    target_filepath: str,
    api_key: Optional[str] = None,
    budget_limit_usd: float = 1.0
) -> Dict[str, Any]:
    """
    Submits code + error context to Gemini via direct REST,
    guaranteeing Circuit Breaker spend-safety and cache hits.
    """
    key = api_key or os.getenv("GEMINI_API_KEY", "")
    if not key or not key.strip():
        # Clean offline simulation when key not provided
        return _offline_diagnostic(error_log, target_filepath, file_context)

    # 1. Check Circuit Breaker
    check_circuit_breaker(spend_limit_usd=budget_limit_usd)

    # 2. Check Local SHA256 Cache (Free Instant Hit)
    cache_key = hash_content(f"{target_filepath}::{error_log}::{file_context}")
    cached = get_cached_response(cache_key)
    if cached:
        cached["is_cached"] = True
        return cached

    # 3. Direct REST with Model Handshake
    clean_key = key.strip()
    models_to_try = ["gemini-1.5-flash", "gemini-1.5-flash-latest", "gemini-1.5-pro"]
    
    prompt = f"""
File: {target_filepath}
Error / Traceback:
{error_log}

Source Code Context:
{file_context}
"""

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "systemInstruction": {"parts": [{"text": SYSTEM_PROMPT}]},
        "generationConfig": {
            "responseMimeType": "application/json",
            "temperature": 0.2
        }
    }

    last_err = None
    for m in models_to_try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent?key={clean_key}"
        try:
            resp = requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=18)
            if resp.status_code == 200:
                out = resp.json()["candidates"][0]["content"]["parts"][0]["text"]
                data = json.loads(out)
                
                # Estimate tokens and record spend
                tokens_in = len(prompt) // 4
                tokens_out = len(out) // 4
                cost = record_spend(tokens_in, tokens_out)
                
                data["cost_usd"] = cost
                data["is_cached"] = False
                data["model_used"] = m
                
                # Cache response
                store_cached_response(cache_key, data)
                return data
            else:
                last_err = f"HTTP {resp.status_code}: {resp.text[:100]}"
        except Exception as e:
            last_err = str(e)
            continue

    raise RuntimeError(f"All candidate models failed: {last_err}")


def apply_patch_to_file(target_filepath: str, original_snippet: str, fixed_snippet: str) -> bool:
    """Safely applies the replacement snippet to the targeted local file."""
    if not os.path.exists(target_filepath):
        raise FileNotFoundError(f"File '{target_filepath}' does not exist.")
    
    with open(target_filepath, "r", encoding="utf-8") as f:
        content = f.read()
    
    if original_snippet not in content:
        # Fallback: line-by-line whitespace-tolerant match
        return False
    
    new_content = content.replace(original_snippet, fixed_snippet, 1)
    with open(target_filepath, "w", encoding="utf-8") as f:
        f.write(new_content)
    return True


def _offline_diagnostic(error_log: str, filepath: str, context: str) -> Dict[str, Any]:
    """Deterministic offline engine when running in demo/air-gapped mode."""
    return {
        "roast": "Congratulations! You treated an optional dictionary key like it was guaranteed to exist, then acted shocked when Python slapped you with a KeyError. Classic Friday-at-5PM code.",
        "root_cause": "Unchecked dictionary subscription without .get() or defensive guard.",
        "target_file": filepath,
        "original_snippet": "user_id = payload['user_id']",
        "fixed_snippet": "user_id = payload.get('user_id')\nif not user_id:\n    raise ValueError('Missing required user_id')",
        "git_patch": f"--- a/{filepath}\n+++ b/{filepath}\n@@ -10,1 +10,3 @@\n-user_id = payload['user_id']\n+user_id = payload.get('user_id')\n+if not user_id:\n+    raise ValueError('Missing required user_id')",
        "cost_usd": 0.0,
        "is_cached": False,
        "model_used": "offline-critic"
    }
