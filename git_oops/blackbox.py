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

DB_DIR = os.path.expanduser("~/.git_oops/memory")
FLIGHT_RECORDER_FILE = os.path.join(DB_DIR, "flight_recorder.jsonl")
ANTIBODIES_FILE = os.path.join(DB_DIR, "antibodies.json")
SNAPSHOTS_DIR = os.path.join(DB_DIR, "snapshots")


def _ensure_dirs():
    os.makedirs(DB_DIR, exist_ok=True)
    os.makedirs(SNAPSHOTS_DIR, exist_ok=True)


def record_step(agent_id: str, action: str, target_file: str, motivation: str, diff: str) -> int:
    """Records an immutable flight recorder event and takes a file snapshot."""
    _ensure_dirs()
    step_id = int(time.time() * 1000)
    
    # Snapshot file
    if os.path.exists(target_file):
        snap_path = os.path.join(SNAPSHOTS_DIR, f"{step_id}_{os.path.basename(target_file)}")
        shutil.copy2(target_file, snap_path)

    event = {
        "step_id": step_id,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "agent_id": agent_id,
        "action": action,
        "target_file": target_file,
        "motivation": motivation,
        "diff_snippet": diff[:300]
    }

    with open(FLIGHT_RECORDER_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(event) + "\n")
    return step_id


def list_flight_events(limit: int = 10) -> List[Dict[str, Any]]:
    """Retrieves recent flight recorder events."""
    _ensure_dirs()
    if not os.path.exists(FLIGHT_RECORDER_FILE):
        return []
    events = []
    with open(FLIGHT_RECORDER_FILE, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                try:
                    events.append(json.loads(line.strip()))
                except Exception:
                    pass
    return events[-limit:]


def rewind_step(step_id: int) -> bool:
    """Restores the targeted file state to match the snapshot taken at step_id."""
    _ensure_dirs()
    events = list_flight_events(limit=100)
    target_event = next((e for e in events if e.get("step_id") == step_id), None)
    if not target_event:
        return False

    orig_file = target_event["target_file"]
    snap_path = os.path.join(SNAPSHOTS_DIR, f"{step_id}_{os.path.basename(orig_file)}")
    if os.path.exists(snap_path):
        shutil.copy2(snap_path, orig_file)
        return True
    return False


def register_antibody(error_pattern: str, verified_solution: str, explanation: str):
    """Stores permanent cross-session immunization pattern."""
    _ensure_dirs()
    antibodies = {}
    if os.path.exists(ANTIBODIES_FILE):
        try:
            with open(ANTIBODIES_FILE, "r", encoding="utf-8") as f:
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

    with open(ANTIBODIES_FILE, "w", encoding="utf-8") as f:
        json.dump(antibodies, f, indent=2)


def match_antibody(error_log: str) -> Optional[Dict[str, Any]]:
    """Returns verified architecture pattern if previously solved in past sessions."""
    _ensure_dirs()
    if not os.path.exists(ANTIBODIES_FILE):
        return None
    try:
        with open(ANTIBODIES_FILE, "r", encoding="utf-8") as f:
            antibodies = json.load(f)
        for _, ab in antibodies.items():
            if ab["pattern"].lower() in error_log.lower():
                return ab
    except Exception:
        pass
    return None
