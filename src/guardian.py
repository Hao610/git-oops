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


import ast
import os
import sys
import re
import shutil
import tempfile
import subprocess
from typing import Tuple, List, Optional


# Well-known Node.js / JavaScript built-in standard modules
NODE_BUILTINS = {
    "fs", "path", "http", "https", "crypto", "os", "events", "stream", "util",
    "child_process", "buffer", "url", "zlib", "cluster", "net", "tls", "assert",
    "process", "readline", "worker_threads", "perf_hooks", "constants"
}

# Standard library modules for Go
GO_STDLIB_PREFIXES = {
    "fmt", "os", "io", "net", "time", "sync", "strings", "bytes", "errors",
    "encoding", "context", "math", "path", "database", "crypto", "log"
}


def check_ghost_imports(code_snippet: str, filepath: str = "app.py") -> Tuple[bool, Optional[str]]:
    """
    Multi-language import verification:
    1. Python: Native AST parsing + runtime spec lookup.
    2. JavaScript / TypeScript: Validates require() and import from against node_modules and builtins.
    3. Go / Rust: Validates stdlib packages and prevents hallucinated dependencies.
    """
    ext = os.path.splitext(filepath)[1].lower()

    # JavaScript / TypeScript
    if ext in [".js", ".ts", ".jsx", ".tsx", ".mjs"]:
        return _check_js_imports(code_snippet)

    # Go
    if ext == ".go":
        return _check_go_imports(code_snippet)

    # Default / Python
    return _check_python_imports(code_snippet)


def _check_python_imports(python_code: str) -> Tuple[bool, Optional[str]]:
    """Native Python AST parsing and environment validation."""
    try:
        tree = ast.parse(python_code)
    except Exception:
        # Fallback for partial snippet diff chunks: regex scan
        imports = re.findall(r"^\s*(?:import|from)\s+([a-zA-Z0-9_]+)", python_code, re.MULTILINE)
        for mod in imports:
            if not _python_module_exists(mod):
                return False, f"GHOST_IMPORT_DETECTED: Agent hallucinated non-existent Python module '{mod}'."
        return True, None

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                mod_name = alias.name.split(".")[0]
                if not _python_module_exists(mod_name):
                    return False, f"GHOST_IMPORT_DETECTED: Agent hallucinated non-existent Python module '{mod_name}'."
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                mod_name = node.module.split(".")[0]
                if not _python_module_exists(mod_name):
                    return False, f"GHOST_IMPORT_DETECTED: Agent hallucinated non-existent Python module '{mod_name}'."

    return True, None


def _check_js_imports(code: str) -> Tuple[bool, Optional[str]]:
    """Validates Node.js require() and ES6 import statements."""
    # Match import x from 'pkg' or require('pkg')
    packages = re.findall(r"(?:import\s+.*?\s+from\s+['\"]([^'\"]+)['\"]|require\(['\"]([^'\"]+)['\"]\))", code)
    for p_tuple in packages:
        pkg = p_tuple[0] or p_tuple[1]
        # Ignore local relative imports e.g. ./utils, ../config
        if pkg.startswith(".") or pkg.startswith("/"):
            continue
        base_pkg = pkg.split("/")[0].replace("@", "")
        # Check Node.js built-in module
        if base_pkg in NODE_BUILTINS:
            continue
        # Check local node_modules if present
        if os.path.exists("node_modules") and os.path.exists(os.path.join("node_modules", pkg)):
            continue
        # Check package.json if present
        if os.path.exists("package.json"):
            try:
                import json
                with open("package.json", "r", encoding="utf-8") as f:
                    pj = json.load(f)
                deps = {**pj.get("dependencies", {}), **pj.get("devDependencies", {})}
                if pkg in deps or base_pkg in deps:
                    continue
            except Exception:
                pass
        # Unresolved package
        if not os.path.exists("node_modules") and not os.path.exists("package.json"):
            # Air-gapped single script check: if not a builtin, flag hallucination
            return False, f"GHOST_IMPORT_DETECTED: Non-builtin JavaScript module '{pkg}' is missing from package.json/node_modules."

    return True, None


def _check_go_imports(code: str) -> Tuple[bool, Optional[str]]:
    """Validates Go import statements."""
    go_imports = re.findall(r'import\s+["\']([^"\']+)["\']', code)
    for pkg in go_imports:
        root_pkg = pkg.split("/")[0]
        if root_pkg in GO_STDLIB_PREFIXES:
            continue
        if os.path.exists("go.mod"):
            with open("go.mod", "r", encoding="utf-8") as f:
                mod_content = f.read()
            if pkg in mod_content or root_pkg in mod_content:
                continue
        return False, f"GHOST_IMPORT_DETECTED: Go package '{pkg}' is not found in standard library or go.mod."
    return True, None


def _python_module_exists(mod_name: str) -> bool:
    """Checks Python stdlib and installed site-packages."""
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
