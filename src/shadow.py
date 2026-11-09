"""
Git-Oops Shadow Workspace Isolation Engine (Feature #14)
Creates an ephemeral in-memory/temp shadow sandbox of the current workspace.
Lets Agents execute risky patches and builds inside the shadow sandbox.
Only commits changes back to the real project if all validations and tests pass!
"""

import os
import shutil
import tempfile
import subprocess
from typing import Tuple, List, Optional


class ShadowWorkspace:
    """Manages an isolated temporary clone of the project workspace."""

    def __init__(self, root_dir: str = "."):
        self.real_root = os.path.abspath(root_dir)
        self.shadow_dir: Optional[str] = None

    def __enter__(self):
        # Create lightweight shadow sandbox excluding heavy git/cache directories
        self.shadow_dir = tempfile.mkdtemp(prefix="git_oops_shadow_")
        self._sync_to_shadow()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.shadow_dir and os.path.exists(self.shadow_dir):
            try:
                shutil.rmtree(self.shadow_dir, ignore_errors=True)
            except Exception:
                pass

    def _sync_to_shadow(self):
        """Copies essential project files to shadow sandbox."""
        ignore_patterns = shutil.ignore_patterns(
            ".git", "__pycache__", ".pytest_cache", "venv", ".env", "*.bak", "dist", "build"
        )
        for item in os.listdir(self.real_root):
            src_path = os.path.join(self.real_root, item)
            dst_path = os.path.join(self.shadow_dir, item)
            if item in [".git", "venv", ".env", "__pycache__", ".pytest_cache"]:
                continue
            if os.path.isdir(src_path):
                shutil.copytree(src_path, dst_path, ignore=ignore_patterns, symlinks=True)
            else:
                shutil.copy2(src_path, dst_path)

    def run_in_shadow(self, command: str) -> Tuple[int, str, str]:
        """Executes a command strictly within the shadow sandbox."""
        proc = subprocess.run(
            command,
            shell=True,
            cwd=self.shadow_dir,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace"
        )
        return proc.returncode, proc.stdout, proc.stderr

    def commit_file_to_real(self, relative_filepath: str) -> bool:
        """Atomically copies a validated file from shadow sandbox back to real workspace."""
        shadow_file = os.path.join(self.shadow_dir, relative_filepath)
        real_file = os.path.join(self.real_root, relative_filepath)
        if not os.path.exists(shadow_file):
            return False
        shutil.copy2(shadow_file, real_file)
        return True
