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

PERSONALITY_PROMPTS = {
    "staff": """You are a cynical, overworked Principal/Staff Software Engineer who has seen too much bad code.
Tone: Cold, brutally direct, technical, deeply disappointed. Sarcastic observations about architecture and lack of discipline.""",
    
    "kernel": """You are a legendary, hot-headed OS kernel maintainer reviewing patch submissions on a public mailing list.
Tone: Volatile, furious, zero tolerance for incompetence. You treat sloppy bugs as an insult to computing history. Use cutting phrases like 'Garbage', 'Brain-damaged architecture', 'What were you thinking?!'""",
    
    "chef": """You are a Michelin-star head chef known for explosive tirades inspecting rotting, undercooked ingredients in a disastrous kitchen.
Tone: Screaming, unhinged, creative culinary analogies. 'This code is so raw it's still running in the field!', 'An idiot sandwich!', 'WAKE UP!'""",
    
    "passive_aggressive": """You are a toxic corporate passive-aggressive senior coworker on Slack.
Tone: Dripping with fake politeness, condescending corporate speak, veiled threats, and extreme snark. 'Per my previous 15 code reviews...', 'Interesting architectural choice, hope you enjoy on-call duty tonight 😊'"""
}


def get_system_prompt(personality: str = "staff") -> str:
    persona_desc = PERSONALITY_PROMPTS.get(personality.lower(), PERSONALITY_PROMPTS["staff"])
    return f"""You are 'git-oops', an AI code reviewer and crash diagnostic engine.
The developer encountered a crash/traceback.

YOUR ROAST PERSONA:
{persona_desc}

RULES:
- Absolutely NO encouragement. No polite filler like 'Hope this helps'.
- The roast must be vicious, witty, and directly target the root technical cause of the error.
- Output strictly valid JSON.

OUTPUT FORMAT REQUIREMENTS:
You MUST respond with valid JSON matching this schema:
{{
  "roast": "<2-3 sentence brutal and witty roast in your chosen persona>",
  "root_cause": "<1 crisp sentence explaining why it broke>",
  "target_file": "<relative path of the file needing fix, e.g. src/app.py>",
  "original_snippet": "<exact original lines of code that need replacement>",
  "fixed_snippet": "<exact replacement code fixing the bug>",
  "git_patch": "<complete unified git diff block starting with '--- a/...' and '+++ b/...'>"
}}
"""


def diagnose_and_patch(
    error_log: str,
    file_context: str,
    target_filepath: str,
    personality: str = "staff",
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
        return _offline_diagnostic(error_log, target_filepath, file_context, personality=personality)

    # 1. Check Circuit Breaker
    check_circuit_breaker(spend_limit_usd=budget_limit_usd)

    # 2. Check Local SHA256 Cache (Free Instant Hit)
    cache_key = hash_content(f"{personality}::{target_filepath}::{error_log}::{file_context}")
    cached = get_cached_response(cache_key)
    if cached:
        cached["is_cached"] = True
        return cached

    # 3. Direct REST with Model Handshake
    clean_key = key.strip()
    # Dynamic model hierarchy: if user supplies custom GEMINI_MODEL, use it first; then standard fallback chain
    custom_model = os.getenv("GEMINI_MODEL", "").strip()
    models_to_try = [custom_model] if custom_model else []
    models_to_try += ["gemini-2.0-flash", "gemini-1.5-flash", "gemini-1.5-pro", "gemini-1.5-flash-latest"]
    
    prompt = f"""
File: {target_filepath}
Error / Traceback:
{error_log}

Source Code Context:
{file_context}
"""

    system_inst = get_system_prompt(personality)
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "systemInstruction": {"parts": [{"text": system_inst}]},
        "generationConfig": {
            "responseMimeType": "application/json",
            "temperature": 0.4
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
    """Safely applies the replacement snippet to the targeted local file and creates a backup."""
    if not os.path.exists(target_filepath):
        raise FileNotFoundError(f"File '{target_filepath}' does not exist.")
    
    with open(target_filepath, "r", encoding="utf-8") as f:
        content = f.read()
    
    if original_snippet not in content:
        # Fallback 1: strip line-ending discrepancies (\r\n vs \n)
        normalized_content = content.replace("\r\n", "\n")
        normalized_orig = original_snippet.replace("\r\n", "\n")
        if normalized_orig in normalized_content:
            content = normalized_content
            original_snippet = normalized_orig
            fixed_snippet = fixed_snippet.replace("\r\n", "\n")
        else:
            return False
    
    # Create backup for rollback support
    backup_path = f"{target_filepath}.oops.bak"
    with open(backup_path, "w", encoding="utf-8") as bkp:
        bkp.write(content)

    new_content = content.replace(original_snippet, fixed_snippet, 1)
    with open(target_filepath, "w", encoding="utf-8") as f:
        f.write(new_content)
    return True


def rollback_file(target_filepath: str) -> bool:
    """Restores a file from its .oops.bak backup."""
    backup_path = f"{target_filepath}.oops.bak"
    if not os.path.exists(backup_path):
        return False
    
    with open(backup_path, "r", encoding="utf-8") as bkp:
        original_content = bkp.read()
    
    with open(target_filepath, "w", encoding="utf-8") as f:
        f.write(original_content)
    
    os.remove(backup_path)
    return True


def _offline_diagnostic(error_log: str, filepath: str, context: str, personality: str = "staff") -> Dict[str, Any]:
    """Deterministic offline engine when running in demo/air-gapped mode."""
    roasts = {
        "staff": "Congratulations! You treated an optional dictionary key like it was guaranteed to exist, then acted shocked when Python slapped you with a KeyError. Classic Friday-at-5PM code.",
        "kernel": "Are you out of your mind?! Accessing an unvalidated map key directly? This isn't just a bug, it's an insult to memory management and everyone who taught you computer science.",
        "chef": "LOOK AT THIS KEYERROR! IT'S RAW! A five-year-old child could write safer dictionary access than this pathetic excuse for code! IDIOT SANDWICH!",
        "passive_aggressive": "Per my previous 15 code reviews, dictionaries can be empty. But clearly writing defensive code was too much effort today. Hope you have fun debugging in production at 3 AM! 😊"
    }
    roast_text = roasts.get(personality.lower(), roasts["staff"])

    return {
        "roast": roast_text,
        "root_cause": "Unchecked dictionary subscription without .get() or defensive guard.",
        "target_file": filepath,
        "original_snippet": "user_id = payload['user_id']",
        "fixed_snippet": "user_id = payload.get('user_id')\nif not user_id:\n    raise ValueError('Missing required user_id')",
        "git_patch": f"--- a/{filepath}\n+++ b/{filepath}\n@@ -10,1 +10,3 @@\n-user_id = payload['user_id']\n+user_id = payload.get('user_id')\n+if not user_id:\n+    raise ValueError('Missing required user_id')",
        "cost_usd": 0.0,
        "is_cached": False,
        "model_used": f"offline-{personality}"
    }
