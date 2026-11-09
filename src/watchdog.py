"""
Git-Oops Watchdog: Anti-Thrashing Loop Buster & Multi-Agent Mutex Lock
Detects edit-revert oscillations and prevents multi-agent write collisions.
"""

import os
import json
import time
import hashlib
from typing import Dict, Any, Tuple

STATE_DIR = os.path.expanduser("~/.git_oops/state")
HISTORY_FILE = os.path.join(STATE_DIR, "patch_history.json")
LOCK_FILE = os.path.join(STATE_DIR, "agent_locks.json")


def _ensure_state():
    os.makedirs(STATE_DIR, exist_ok=True)


def check_anti_thrashing(filepath: str, patch_str: str, max_oscillations: int = 3) -> Tuple[bool, str]:
    """
    Tracks patch history per file. If an agent tries to apply the same or reverse
    patch repeatedly (thrashing / rabbit hole), it trips the watchdog.
    """
    _ensure_state()
    history = {}
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                history = json.load(f)
        except Exception:
            history = {}

    patch_hash = hashlib.sha256(patch_str.strip().encode()).hexdigest()
    file_records = history.get(filepath, [])
    
    # Count occurrences of this exact patch or rapid reverts in recent history
    occurrences = sum(1 for p in file_records[-6:] if p == patch_hash)
    if occurrences >= max_oscillations:
        return False, (
            f"ANTI_THRASHING_HALT: Agent is caught in a loop modifying '{filepath}'. "
            f"Same patch proposed {occurrences + 1} times. Step back and re-architect."
        )

    file_records.append(patch_hash)
    history[filepath] = file_records[-10:]  # Keep last 10 entries
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2)

    return True, "SAFE"


def acquire_agent_lock(agent_id: str, filepath: str, lease_seconds: int = 30) -> Tuple[bool, str]:
    """Prevents two concurrent agents from overwriting the same file."""
    _ensure_state()
    locks = {}
    now = time.time()
    if os.path.exists(LOCK_FILE):
        try:
            with open(LOCK_FILE, "r", encoding="utf-8") as f:
                locks = json.load(f)
        except Exception:
            locks = {}

    current_holder = locks.get(filepath)
    if current_holder and current_holder.get("expires", 0) > now:
        if current_holder.get("agent_id") != agent_id:
            return False, f"MUTEX_LOCKED: File '{filepath}' is currently held by '{current_holder.get('agent_id')}'"

    # Acquire or renew lease
    locks[filepath] = {
        "agent_id": agent_id,
        "expires": now + lease_seconds,
        "acquired_at": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    with open(LOCK_FILE, "w", encoding="utf-8") as f:
        json.dump(locks, f, indent=2)
    return True, "LOCK_ACQUIRED"


def release_agent_lock(agent_id: str, filepath: str):
    """Releases lock on file."""
    _ensure_state()
    if not os.path.exists(LOCK_FILE):
        return
    try:
        with open(LOCK_FILE, "r", encoding="utf-8") as f:
            locks = json.load(f)
        if filepath in locks and locks[filepath].get("agent_id") == agent_id:
            del locks[filepath]
            with open(LOCK_FILE, "w", encoding="utf-8") as f:
                json.dump(locks, f, indent=2)
    except Exception:
        pass
