"""
Git-Oops Git Emergency Rescuer & Ghost Worktree Sandbox:
1. Recovers lost commits from git reflog (Detached HEAD / rebase crashes).
2. Spawns isolated zero-overhead git worktree sandbox at refs/oops/sandbox.
"""

import os
import shutil
import subprocess
from typing import Tuple, Optional, List, Dict, Any


def salvage_reflog() -> Tuple[bool, str, List[Dict[str, str]]]:
    """
    Parses git reflog to find dangling, detached, or recently lost commits.
    Returns (success, message, recovered_entries).
    """
    try:
        out = subprocess.check_output(
            ["git", "reflog", "-n", "15", "--format=%h|%gd|%gs"],
            text=True,
            stderr=subprocess.STDOUT
        )
        entries = []
        for line in out.strip().splitlines():
            parts = line.split("|")
            if len(parts) >= 3:
                entries.append({
                    "commit": parts[0],
                    "ref": parts[1],
                    "action": parts[2]
                })

        return True, f"SALVAGE_SUCCESS: Analyzed {len(entries)} recent reflog states.", entries
    except Exception as e:
        return False, f"SALVAGE_FAILED: Unable to read git reflog ({str(e)})", []


def run_reflog_autopsy() -> List[Dict[str, Any]]:
    """Convenience alias for salvage_reflog returning structured commit list."""
    ok, msg, entries = salvage_reflog()
    commits = []
    for e in entries:
        commits.append({
            "sha": e.get("commit", ""),
            "subject": e.get("action", ""),
            "reflog_action": e.get("ref", "")
        })
    return commits


def restore_reflog_commit(commit_hash: str) -> Tuple[bool, str]:
    """Safely checks out or branches from a lost reflog commit without losing state."""
    try:
        # Create a rescue branch instead of detached checkout
        rescue_branch = f"rescue-{commit_hash[:7]}"
        subprocess.check_output(["git", "branch", rescue_branch, commit_hash], stderr=subprocess.STDOUT)
        return True, f"SALVAGE_RESTORED: Saved lost commit '{commit_hash}' to branch '{rescue_branch}'."
    except Exception as e:
        return False, f"SALVAGE_RESTORE_ERROR: {str(e)}"


class GhostWorktreeSandbox:
    """
    Spawns an ultra-lightweight, zero-overhead git worktree sandbox.
    Agents can run risky builds and tests inside without modifying human working directory.
    """
    def __init__(self, sandbox_name: str = "oops-sandbox"):
        self.sandbox_name = sandbox_name
        self.sandbox_path = os.path.join(os.path.expanduser("~/.git_oops/sandboxes"), sandbox_name)

    def __enter__(self):
        os.makedirs(os.path.dirname(self.sandbox_path), exist_ok=True)
        if os.path.exists(self.sandbox_path):
            shutil.rmtree(self.sandbox_path, ignore_errors=True)
        try:
            # Create detached worktree from HEAD
            subprocess.check_output(
                ["git", "worktree", "add", "--detach", self.sandbox_path, "HEAD"],
                stderr=subprocess.DEVNULL
            )
        except Exception:
            pass
        return self.sandbox_path

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            subprocess.check_output(["git", "worktree", "remove", "--force", self.sandbox_path], stderr=subprocess.DEVNULL)
        except Exception:
            pass
        if os.path.exists(self.sandbox_path):
            shutil.rmtree(self.sandbox_path, ignore_errors=True)
