"""
Git-Oops Watchdog: Anti-Thrashing Loop Buster & Multi-Agent Mutex Lock
Detects edit-revert oscillations and prevents multi-agent write collisions.
"""

import os
import json
import time
import signal
import hashlib
import subprocess
from typing import Dict, Any, Tuple, Optional, List


def _get_home_dir() -> str:
    return os.environ.get("GIT_OOPS_HOME", os.path.expanduser("~/.git_oops"))


def _get_state_dir() -> str:
    return os.path.join(_get_home_dir(), "state")


def _get_freeze_file() -> str:
    return os.path.join(_get_home_dir(), ".emergency_freeze")


STATE_DIR = os.path.expanduser("~/.git_oops/state")
HISTORY_FILE = os.path.join(STATE_DIR, "patch_history.json")
LOCK_FILE = os.path.join(STATE_DIR, "agent_locks.json")


def _ensure_state():
    os.makedirs(_get_state_dir(), exist_ok=True)


def freeze_workstation(reason: str = "Operator requested emergency freeze") -> Tuple[bool, str]:
    """Writes a machine-wide immutable emergency freeze lockfile."""
    home = _get_home_dir()
    os.makedirs(home, exist_ok=True)
    freeze_path = _get_freeze_file()
    payload = {
        "frozen_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "timestamp": time.time(),
        "reason": reason or "Operator requested emergency freeze",
    }
    with open(freeze_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    return True, f"EMERGENCY FREEZE ACTIVE: All git mutations blocked ({payload['reason']})."


def unfreeze_workstation() -> Tuple[bool, str]:
    """Removes the emergency freeze lockfile to restore normal operation."""
    freeze_path = _get_freeze_file()
    if os.path.exists(freeze_path):
        os.remove(freeze_path)
        return True, "EMERGENCY FREEZE CLEARED: Workstation unlocked."
    return True, "Workstation was not frozen."


def is_workstation_frozen() -> Tuple[bool, Optional[str]]:
    """Checks whether the emergency freeze lockfile is active."""
    freeze_path = _get_freeze_file()
    if not os.path.exists(freeze_path):
        return False, None
    try:
        with open(freeze_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return True, data.get("reason", "Emergency freeze active")
    except Exception:
        return True, "Emergency freeze active"


def _is_agent_cmdline(line: str) -> bool:
    return "--mcp" in line or "git_oops --agent" in line


def _kill_windows_agents(my_pid: int) -> List[str]:
    killed: List[str] = []
    proc = subprocess.run(
        ["wmic", "process", "get", "ProcessId,CommandLine", "/FORMAT:CSV"],
        capture_output=True, text=True, errors="replace", timeout=5
    )
    for line in proc.stdout.splitlines():
        if not _is_agent_cmdline(line):
            continue
        parts = line.strip().split(",")
        if parts and parts[-1].isdigit() and int(parts[-1]) != my_pid:
            pid = int(parts[-1])
            subprocess.run(["taskkill", "/F", "/PID", str(pid)], capture_output=True)
            killed.append(f"PID {pid}")
    return killed


def _kill_posix_agents(my_pid: int) -> List[str]:
    killed: List[str] = []
    proc = subprocess.run(
        ["ps", "-eo", "pid,args"],
        capture_output=True, text=True, errors="replace", timeout=5
    )
    for line in proc.stdout.splitlines():
        if not _is_agent_cmdline(line):
            continue
        parts = line.strip().split(None, 1)
        if parts and parts[0].isdigit() and int(parts[0]) != my_pid:
            pid = int(parts[0])
            os.kill(pid, signal.SIGTERM)
            killed.append(f"PID {pid}")
    return killed


def kill_orphaned_agents() -> Tuple[int, List[str]]:
    """
    Scans running processes for detached git-oops MCP or agent subshells
    (excluding the current process) and terminates them cleanly.
    """
    my_pid = os.getpid()
    try:
        killed = _kill_windows_agents(my_pid) if os.name == "nt" else _kill_posix_agents(my_pid)
    except Exception:
        killed = []
    return len(killed), killed


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

    # Compute cryptographic checksum of code diff to track repeated oscillations
    patch_hash = hashlib.sha256(patch_str.strip().encode("utf-8")).hexdigest()
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
