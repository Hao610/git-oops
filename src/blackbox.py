"""
Git-Oops Blackbox & Memory: Flight Recorder, Time-Machine Rewind & Antibody DB
1. Flight Recorder: Logs agent intentions, tools invoked, and patches applied.
2. Time-Machine: Rewinds codebase state to any previous step.
3. Antibody DB: Persistent cross-session immunization patterns.
"""

import os
import json
import time
import shutil
import hashlib
from typing import Dict, Any, List, Optional


def get_memory_dir() -> str:
    """Returns directory for blackbox memory, supporting isolated test sandboxes."""
    return os.environ.get("GIT_OOPS_MEMORY_DIR", os.path.expanduser("~/.git_oops/memory"))


def get_flight_recorder_file() -> str:
    return os.path.join(get_memory_dir(), "flight_recorder.jsonl")


def get_antibodies_file() -> str:
    return os.path.join(get_memory_dir(), "antibodies.json")


def get_snapshots_dir() -> str:
    return os.path.join(get_memory_dir(), "snapshots")


def _ensure_dirs():
    os.makedirs(get_memory_dir(), exist_ok=True)
    os.makedirs(get_snapshots_dir(), exist_ok=True)


def record_step(agent_id: str, action: str, target_file: str, motivation: str, diff: str) -> int:
    """Records an immutable flight recorder event and takes a file snapshot."""
    _ensure_dirs()
    step_id = int(time.time() * 1000)
    
    # Snapshot file
    if target_file and os.path.exists(target_file):
        snap_path = os.path.join(get_snapshots_dir(), f"{step_id}_{os.path.basename(target_file)}")
        try:
            shutil.copy2(target_file, snap_path)
        except Exception:
            pass

    # Enterprise sanitation
    clean_agent = (agent_id or "autonomous-agent").strip()
    if clean_agent.lower() in ("undefined", "none", ""):
        clean_agent = "autonomous-agent"

    event = {
        "step_id": step_id,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "agent_id": clean_agent,
        "actor": clean_agent,
        "action": action,
        "target_file": target_file,
        "motivation": motivation,
        "diff_snippet": diff[:300] if diff else ""
    }

    with open(get_flight_recorder_file(), "a", encoding="utf-8") as f:
        f.write(json.dumps(event) + "\n")
    return step_id


def list_flight_events(limit: int = 10) -> List[Dict[str, Any]]:
    """Retrieves recent flight recorder events."""
    _ensure_dirs()
    flight_file = get_flight_recorder_file()
    if not os.path.exists(flight_file):
        return []
    events = []
    with open(flight_file, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                try:
                    events.append(json.loads(line.strip()))
                except Exception:
                    pass
    return events[-limit:]


def clear_flight_events() -> bool:
    """Clears all recorded flight events and snapshots."""
    _ensure_dirs()
    flight_file = get_flight_recorder_file()
    if os.path.exists(flight_file):
        try:
            with open(flight_file, "w", encoding="utf-8") as f:
                pass
            return True
        except Exception:
            return False
    return True


def rewind_step(step_id: int) -> bool:
    """Restores the targeted file state to match the snapshot taken at step_id."""
    _ensure_dirs()
    events = list_flight_events(limit=100)
    target_event = next((e for e in events if e.get("step_id") == step_id), None)
    if not target_event:
        return False

    orig_file = target_event["target_file"]
    snap_path = os.path.join(get_snapshots_dir(), f"{step_id}_{os.path.basename(orig_file)}")
    if os.path.exists(snap_path):
        shutil.copy2(snap_path, orig_file)
        return True
    return False


def register_antibody(error_pattern: str, verified_solution: str, explanation: str):
    """Stores permanent cross-session immunization pattern."""
    _ensure_dirs()
    antibodies_file = get_antibodies_file()
    antibodies = {}
    if os.path.exists(antibodies_file):
        try:
            with open(antibodies_file, "r", encoding="utf-8") as f:
                antibodies = json.load(f)
        except Exception:
            antibodies = {}

    pat_hash = hashlib.sha256(error_pattern.strip().lower().encode()).hexdigest()[:16]
    antibodies[pat_hash] = {
        "pattern": error_pattern.strip(),
        "solution": verified_solution,
        "explanation": explanation,
        "learned_at": time.strftime("%Y-%m-%d")
    }

    with open(antibodies_file, "w", encoding="utf-8") as f:
        json.dump(antibodies, f, indent=2)


def match_antibody(error_trace: str) -> Optional[Dict[str, str]]:
    """Checks if an error matches any known pre-immunized antibody."""
    antibodies_file = get_antibodies_file()
    if not os.path.exists(antibodies_file):
        return None
    try:
        with open(antibodies_file, "r", encoding="utf-8") as f:
            antibodies = json.load(f)
    except Exception:
        return None

    norm_trace = error_trace.strip().lower()
    for _, anti in antibodies.items():
        if anti["pattern"].lower() in norm_trace:
            return anti
    return None
