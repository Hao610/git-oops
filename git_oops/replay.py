"""
Git-Oops Post-Mortem Crash Replay Time-Machine:
Reconstructs terminal variables, locals, and scope right at the moment of the crash.
Zero dependencies: Uses native traceback inspections and saved snapshot states.
"""

import os
import sys
import json
import traceback
from typing import Dict, Any, Optional

CRASH_SNAPSHOT_DIR = os.path.expanduser("~/.git_oops/crashes")


def record_crash_scope(filepath: str, error_log: str, local_vars: Optional[Dict[str, Any]] = None):
    """Saves post-mortem scope variables to local storage."""
    os.makedirs(CRASH_SNAPSHOT_DIR, exist_ok=True)
    clean_locals = {}
    if local_vars:
        for k, v in local_vars.items():
            if not k.startswith("__"):
                clean_locals[k] = str(v)[:150]

    record = {
        "timestamp": os.path.getmtime(filepath) if os.path.exists(filepath) else 0,
        "filepath": filepath,
        "error_log": error_log.strip()[:1000],
        "locals": clean_locals
    }
    
    snap_file = os.path.join(CRASH_SNAPSHOT_DIR, "last_crash.json")
    with open(snap_file, "w", encoding="utf-8") as f:
        json.dump(record, f, indent=2)


def get_last_crash_replay() -> Optional[Dict[str, Any]]:
    """Loads the last recorded post-mortem crash state."""
    snap_file = os.path.join(CRASH_SNAPSHOT_DIR, "last_crash.json")
    if not os.path.exists(snap_file):
        return None
    try:
        with open(snap_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def record_crash_snapshot(
    target_file: str,
    exception_type: str,
    exception_message: str,
    stack_frames: list = None,
    local_vars: Optional[Dict[str, Any]] = None
) -> str:
    """Records detailed crash snapshot into ~/.git_oops/crashes/<id>.json."""
    os.makedirs(CRASH_SNAPSHOT_DIR, exist_ok=True)
    import time
    snap_id = f"crash_{int(time.time() * 1000)}.json"
    clean_locals = {}
    if local_vars:
        for k, v in local_vars.items():
            if not k.startswith("__"):
                clean_locals[k] = v

    data = {
        "snapshot_id": snap_id,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "target_file": target_file,
        "exception_type": exception_type,
        "exception_message": exception_message,
        "stack_frames": stack_frames or [],
        "local_variables": clean_locals
    }
    with open(os.path.join(CRASH_SNAPSHOT_DIR, snap_id), "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    # Also link as last_crash.json
    with open(os.path.join(CRASH_SNAPSHOT_DIR, "last_crash.json"), "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    return snap_id


def inspect_crash_snapshot(snap_id: str = "last_crash.json") -> Dict[str, Any]:
    """Inspects a recorded crash snapshot."""
    target_path = os.path.join(CRASH_SNAPSHOT_DIR, snap_id) if not os.path.isabs(snap_id) else snap_id
    if not os.path.exists(target_path):
        return {"status": "NOT_FOUND", "path": target_path}
    try:
        with open(target_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        return {"status": "ERROR", "details": str(e)}


def list_crash_snapshots(limit: int = 10) -> list:
    """Lists recent crash snapshots."""
    if not os.path.exists(CRASH_SNAPSHOT_DIR):
        return []
    files = sorted([f for f in os.listdir(CRASH_SNAPSHOT_DIR) if f.startswith("crash_") and f.endswith(".json")], reverse=True)
    return files[:limit]
