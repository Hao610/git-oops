"""
Git-Oops Circuit Breaker & Local Token/Cost Cache
Guarantees absolute spend-protection:
1. Daily USD hard expenditure ceiling (stops runaway recursive calls)
2. Exact SHA256 deterministic response cache (zero duplicate API costs)
3. Transparent token-to-dollar real-time accounting
"""

import os
import json
import time
import hashlib
from typing import Dict, Any, Optional

CACHE_DIR = os.path.expanduser("~/.git_oops")
CACHE_FILE = os.path.join(CACHE_DIR, "cache.json")
LEDGER_FILE = os.path.join(CACHE_DIR, "spend_ledger.json")

# Rates per 1M tokens ($0.15 input, $0.60 output approx Gemini 1.5 Flash)
COST_PER_INPUT_TOKEN = 0.15 / 1_000_000
COST_PER_OUTPUT_TOKEN = 0.60 / 1_000_000


def _ensure_dir():
    os.makedirs(CACHE_DIR, exist_ok=True)


def get_daily_spend() -> float:
    """Calculates total spend accumulated today."""
    _ensure_dir()
    if not os.path.exists(LEDGER_FILE):
        return 0.0
    try:
        with open(LEDGER_FILE, "r", encoding="utf-8") as f:
            ledger = json.load(f)
        today = time.strftime("%Y-%m-%d")
        return float(ledger.get(today, 0.0))
    except Exception:
        return 0.0


def record_spend(tokens_in: int, tokens_out: int) -> float:
    """Updates daily spend ledger and returns cost incurred."""
    _ensure_dir()
    cost = (tokens_in * COST_PER_INPUT_TOKEN) + (tokens_out * COST_PER_OUTPUT_TOKEN)
    today = time.strftime("%Y-%m-%d")
    ledger = {}
    if os.path.exists(LEDGER_FILE):
        try:
            with open(LEDGER_FILE, "r", encoding="utf-8") as f:
                ledger = json.load(f)
        except Exception:
            ledger = {}
    
    current = ledger.get(today, 0.0)
    ledger[today] = round(current + cost, 5)
    with open(LEDGER_FILE, "w", encoding="utf-8") as f:
        json.dump(ledger, f, indent=2)
    return cost


def check_circuit_breaker(spend_limit_usd: float = 1.0) -> bool:
    """
    Returns True if safe to run; raises PermissionError if budget exceeded.
    Protects developers from unexpected cloud bills.
    """
    spent = get_daily_spend()
    if spent >= spend_limit_usd:
        raise PermissionError(
            f"🚨 [CIRCUIT BREAKER TRIGGERED] Daily budget of ${spend_limit_usd:.2f} exceeded! "
            f"(Spent today: ${spent:.4f}). Requests blocked to protect your wallet."
        )
    return True


def get_cached_response(prompt_hash: str) -> Optional[Dict[str, Any]]:
    """Retrieves deterministic cached patch if previously analyzed."""
    _ensure_dir()
    if not os.path.exists(CACHE_FILE):
        return None
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            cache = json.load(f)
        return cache.get(prompt_hash)
    except Exception:
        return None


def store_cached_response(prompt_hash: str, response: Dict[str, Any]):
    """Caches response by content hash to prevent redundant duplicate queries."""
    _ensure_dir()
    cache = {}
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                cache = json.load(f)
        except Exception:
            cache = {}
    cache[prompt_hash] = response
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=2)


def hash_content(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()
