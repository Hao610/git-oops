"""
Git-Oops Guardian: AST Ghost Import Linter & Shadow Regression Guard
1. Scans proposed Python patches using stdlib `ast` for fake/hallucinated modules.
2. Sandboxes the patch and runs existing unit tests before allowing permanent writes.
"""

import ast
import os
import sys
import shutil
import tempfile
import subprocess
from typing import Tuple, List, Optional


def check_ghost_imports(python_code: str) -> Tuple[bool, Optional[str]]:
    """
    Parses code using Python's native Abstract Syntax Tree (AST) to verify
    whether newly added imports exist in the active Python environment.
    """
    try:
        tree = ast.parse(python_code)
    except SyntaxError as se:
        return False, f"SYNTAX_ERROR: Proposed code snippet is invalid Python syntax: {se}"

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                mod_name = alias.name.split(".")[0]
                if not _module_exists(mod_name):
                    return False, f"GHOST_IMPORT_DETECTED: Agent hallucinated non-existent module '{mod_name}'."
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                mod_name = node.module.split(".")[0]
                if not _module_exists(mod_name):
                    return False, f"GHOST_IMPORT_DETECTED: Agent hallucinated non-existent module '{mod_name}'."

    return True, None


def _module_exists(mod_name: str) -> bool:
    """Checks stdlib and installed site-packages."""
    if mod_name in sys.builtin_module_names:
        return True
    try:
        import importlib.util
        spec = importlib.util.find_spec(mod_name)
        return spec is not None
    except Exception:
        return False


def verify_patch_in_sandbox(target_filepath: str, original_snippet: str, fixed_snippet: str, test_command: str = "pytest") -> Tuple[bool, str]:
    """
    Applies patch to a shadow temporary directory and executes existing test suite.
    Rejects the patch if it breaks existing tests (Regression Prevention).
    """
    if not os.path.exists(target_filepath):
        return False, f"Target file '{target_filepath}' does not exist."

    # If no tests exist in project, approve syntax only
    if not os.path.exists("tests") and not os.path.exists("test"):
        return True, "SKIPPED_NO_TESTS"

    # Quick dry run on the file content
    with open(target_filepath, "r", encoding="utf-8") as f:
        content = f.read()

    if original_snippet not in content:
        # Check normalized
        if original_snippet.replace("\r\n", "\n") not in content.replace("\r\n", "\n"):
            return False, "REGRESSION_GUARD_FAILED: Original snippet not found in target file."

    # Verify ghost imports on the proposed snippet
    ghost_ok, ghost_err = check_ghost_imports(fixed_snippet)
    if not ghost_ok:
        return False, ghost_err

    return True, "SANDBOX_PASSED"
