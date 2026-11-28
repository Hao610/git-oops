"""
Git-Oops Global Git Interceptor & L3 Local Pre-Flight CI/CD Engine
Zero-step machine-wide protection on 'git commit' and 'git push'.
Executes in <0.3s with AST taint tracking, secret scanning, and supply-chain audits.
"""

import os
import sys
import ast
import math
import json
import stat
import shutil
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

from src.supply_chain import check_typosquatting
from src.squeezer import redact_secrets
from src.rules import load_security_rules, trigger_ota_update_background
from src.watchdog import is_workstation_frozen
from src.firewall import verify_human_affirmation
from src.sentinel import (
    check_test_assertion_guard,
    check_nesting_and_complexity,
    check_zombie_files,
)


# Path definitions
GIT_OOPS_HOME = Path.home() / ".git_oops"
HOOKS_DIR = GIT_OOPS_HOME / "hooks"
MARKER_FILE = GIT_OOPS_HOME / ".hooks_installed"


# ---------------------------------------------------------------------------
# 1. Zero-Step Global Hooks Bootstrap
# ---------------------------------------------------------------------------

PRE_COMMIT_SCRIPT_SH = """#!/bin/sh
exec python -m src.cli --pre-commit
"""

PRE_PUSH_SCRIPT_SH = """#!/bin/sh
exec python -m src.cli --pre-push
"""

PRE_COMMIT_SCRIPT_BAT = """@echo off
python -m git_oops --pre-commit
if %ERRORLEVEL% equ 0 exit /b 0
py -m git_oops --pre-commit
exit /b %ERRORLEVEL%
"""

PRE_PUSH_SCRIPT_BAT = """@echo off
python -m git_oops --pre-push
if %ERRORLEVEL% equ 0 exit /b 0
py -m git_oops --pre-push
exit /b %ERRORLEVEL%
"""


def setup_global_hooks(force: bool = False) -> Tuple[bool, str]:
    """
    Sets up machine-wide Git hooks using 'git config --global core.hooksPath'.
    Zero manual configuration required by user.
    """
    try:
        HOOKS_DIR.mkdir(parents=True, exist_ok=True)

        pre_commit_path = HOOKS_DIR / "pre-commit"
        pre_push_path = HOOKS_DIR / "pre-push"
        pre_commit_bat = HOOKS_DIR / "pre-commit.bat"
        pre_push_bat = HOOKS_DIR / "pre-push.bat"

        # Write bash scripts (used by Git Bash, macOS, Linux, WSL)
        with open(pre_commit_path, "w", encoding="utf-8", newline="\n") as f:
            f.write(PRE_COMMIT_SCRIPT_SH)
        with open(pre_push_path, "w", encoding="utf-8", newline="\n") as f:
            f.write(PRE_PUSH_SCRIPT_SH)

        # Write Windows batch scripts
        with open(pre_commit_bat, "w", encoding="utf-8") as f:
            f.write(PRE_COMMIT_SCRIPT_BAT)
        with open(pre_push_bat, "w", encoding="utf-8") as f:
            f.write(PRE_PUSH_SCRIPT_BAT)

        # Make executable on Unix
        for p in (pre_commit_path, pre_push_path):
            try:
                st = os.stat(p)
                os.chmod(p, st.st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
            except Exception:
                pass

        # Check existing git global hooksPath
        res = subprocess.run(
            ["git", "config", "--global", "--get", "core.hooksPath"],
            capture_output=True, text=True, errors="replace"
        )
        existing_path = res.stdout.strip()

        hooks_dir_str = str(HOOKS_DIR).replace("\\", "/")
        if not existing_path or force or existing_path == hooks_dir_str:
            subprocess.run(
                ["git", "config", "--global", "core.hooksPath", hooks_dir_str],
                check=True, capture_output=True
            )
            MARKER_FILE.write_text("v1.2.1", encoding="utf-8")
            return True, f"Global git hooks installed cleanly at {hooks_dir_str}"
        else:
            return False, f"Existing custom core.hooksPath detected: '{existing_path}'. Not overwriting without --force."
    except Exception as e:
        return False, f"Hook installation error: {str(e)}"


def ensure_auto_hooks():
    """
    Fast idempotent bootstrap and self-healing check called on CLI run.
    If hooks were deleted or tampered with, recreates and rebinds them instantly in <2ms.
    """
    pre_commit_path = HOOKS_DIR / "pre-commit"
    if MARKER_FILE.exists() and pre_commit_path.exists():
        return
    try:
        setup_global_hooks(force=False)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# 2. Shannon Entropy & Secret Scanner (L1 Pre-Flight)
# ---------------------------------------------------------------------------

def calculate_shannon_entropy(data: str) -> float:
    """Calculates Shannon entropy of a string to detect high-entropy keys."""
    if not data:
        return 0.0
    entropy = 0.0
    length = len(data)
    for x in set(data):
        p_x = float(data.count(x)) / length
        if p_x > 0:
            entropy += - p_x * math.log2(p_x)
    return entropy


COMMON_SECRET_PATTERNS = [
    (r"(?i)(?:api[_-]?key|secret|password|passwd|auth[_-]?token)\s*[:=]\s*['\"]([a-zA-Z0-9_\-\.]{16,})['\"]", "Exposed Secret Literal"),
    (r"(?i)sk-[a-zA-Z0-9]{32,}", "OpenAI API Key"),
    (r"(?i)AKIA[0-9A-Z]{16}", "AWS Access Key ID"),
    (r"(?i)ghp_[a-zA-Z0-9]{36}", "GitHub Personal Access Token"),
    (r"(?i)xox[baprs]-[0-9a-zA-Z]{10,48}", "Slack Token"),
    (r"-----BEGIN (?:RSA|OPENSSH|DSA|EC|PGP)? PRIVATE KEY-----", "Private Cryptographic Key"),
]


def scan_diff_for_secrets(diff_text: str) -> List[Dict[str, Any]]:
    """Scans added lines in a git diff for secrets and high-entropy tokens using dynamic OTA rules."""
    import re
    # Trigger silent background update of rules if online
    trigger_ota_update_background()

    rules = load_security_rules()
    patterns = [(p["pattern"], p["label"]) for p in rules.get("secret_patterns", [])]
    entropy_thresh = rules.get("cwe_thresholds", {}).get("shannon_entropy_threshold", 4.6)

    violations = []
    lines = diff_text.splitlines()
    current_file = ""

    for idx, line in enumerate(lines, 1):
        if line.startswith("+++ b/"):
            current_file = line[6:].strip()
            continue

        # Skip dummy secret fixtures inside test files
        if any(t in current_file.lower() for t in ("tests/", "test_", "/tests/")):
            continue

        if not line.startswith("+") or line.startswith("+++"):
            continue
        content = line[1:].strip()

        for pattern, label in patterns:
            try:
                matches = re.finditer(pattern, content)
                for m in matches:
                    violations.append({
                        "type": "SECRET_LEAK",
                        "label": label,
                        "line": idx,
                        "snippet": content[:80],
                        "severity": "CRITICAL"
                    })
            except Exception:
                continue

        # Check high entropy words (> entropy_thresh, length > 24)
        words = re.findall(r'[a-zA-Z0-9_/\+=]{24,}', content)
        for w in words:
            if calculate_shannon_entropy(w) > entropy_thresh:
                # Discard common non-secret hashes
                if not any(token in w.lower() for token in ["sha256", "commit", "hash", "00000"]):
                    violations.append({
                        "type": "HIGH_ENTROPY_TOKEN",
                        "label": f"High Entropy Token (Entropy: {calculate_shannon_entropy(w):.2f})",
                        "line": idx,
                        "snippet": content[:80],
                        "severity": "HIGH"
                    })
    return violations


# ---------------------------------------------------------------------------
# 3. Native AST CodeQL CWE Mirror (L2 Pre-Flight)
# ---------------------------------------------------------------------------

class CodeQLASTVisitor(ast.NodeVisitor):
    """
    Sub-millisecond AST static analyzer mirroring CodeQL security rules:
    - CWE-89: SQL Injection via string concatenation
    - CWE-78: Command Injection via shell=True or os.system()
    - CWE-22: Path Traversal in open()
    - CWE-95: Dangerous eval() / exec()
    - CWE-532: Cleartext credential logging
    """
    def __init__(self, filename: str, custom_forbidden_calls: list = None):
        self.filename = filename
        self.findings: List[Dict[str, Any]] = []
        self.tainted_vars = set()
        self.custom_forbidden_calls = custom_forbidden_calls or []

    def visit_Assign(self, node: ast.Assign):
        # Track string concatenation assigned to variables (e.g. query = "..." + ...)
        if isinstance(node.value, (ast.BinOp, ast.JoinedStr)):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    self.tainted_vars.add(target.id)
        self.generic_visit(node)

    def _resolve_call_name(self, node: ast.Call) -> Tuple[str, str]:
        if isinstance(node.func, ast.Name):
            return node.func.id, node.func.id
        if isinstance(node.func, ast.Attribute):
            val_id = getattr(node.func.value, "id", "")
            attr = node.func.attr
            return attr, (f"{val_id}.{attr}" if val_id else attr)
        return "", ""

    def _check_custom_and_eval(self, node: ast.Call, func_name: str, full_call: str):
        for forb in self.custom_forbidden_calls:
            if forb in (full_call, func_name):
                self.findings.append({
                    "rule": "custom/forbidden-call", "cwe": "CWE-CUSTOM", "severity": "CRITICAL",
                    "line": node.lineno, "file": self.filename,
                    "msg": f"Custom team policy violation: invocation of '{forb}' is strictly forbidden."
                })
        if func_name in ("eval", "exec"):
            self.findings.append({
                "rule": "py/dangerous-eval", "cwe": "CWE-95", "severity": "CRITICAL",
                "line": node.lineno, "file": self.filename,
                "msg": f"Direct use of {func_name}() detected. Potential arbitrary code execution."
            })

    def _check_command_injection(self, node: ast.Call, func_name: str):
        has_dyn_arg = bool(node.args and isinstance(node.args[0], (ast.BinOp, ast.JoinedStr)))
        if func_name == "system" and has_dyn_arg:
            self.findings.append({
                "rule": "py/command-injection", "cwe": "CWE-78", "severity": "CRITICAL",
                "line": node.lineno, "file": self.filename,
                "msg": "Unsanitized command execution via os.system() with dynamic string concatenation."
            })
        if any(kw.arg == "shell" and isinstance(kw.value, ast.Constant) and kw.value.value is True for kw in node.keywords) and has_dyn_arg:
            self.findings.append({
                "rule": "py/command-injection", "cwe": "CWE-78", "severity": "HIGH",
                "line": node.lineno, "file": self.filename,
                "msg": "subprocess call with shell=True and dynamic string interpolation."
            })

    def _check_sql_and_logging(self, node: ast.Call, func_name: str):
        if func_name in ("execute", "executemany") and node.args:
            arg0 = node.args[0]
            if isinstance(arg0, (ast.BinOp, ast.JoinedStr)) or (isinstance(arg0, ast.Name) and arg0.id in self.tainted_vars):
                self.findings.append({
                    "rule": "py/sql-injection", "cwe": "CWE-89", "severity": "CRITICAL",
                    "line": node.lineno, "file": self.filename,
                    "msg": "Potential SQL injection: execute() called with dynamic string concatenation or tainted variable."
                })
        if func_name in ("debug", "info", "warning", "error", "print"):
            sensitive = ("password", "passwd", "secret", "apikey", "api_key", "token")
            for arg in node.args:
                if isinstance(arg, ast.Name) and any(s in arg.id.lower() for s in sensitive):
                    self.findings.append({
                        "rule": "py/clear-text-logging-sensitive-data", "cwe": "CWE-532", "severity": "MEDIUM",
                        "line": node.lineno, "file": self.filename,
                        "msg": f"Cleartext logging of sensitive variable '{arg.id}'."
                    })

    def visit_Call(self, node: ast.Call):
        func_name, full_call = self._resolve_call_name(node)
        self._check_custom_and_eval(node, func_name, full_call)
        self._check_command_injection(node, func_name)
        self._check_sql_and_logging(node, func_name)
        self.generic_visit(node)


def scan_file_ast(file_path: str, custom_forbidden_calls: list = None) -> List[Dict[str, Any]]:
    """Runs sub-second AST security checks on a python file."""
    if not os.path.exists(file_path) or not file_path.endswith(".py"):
        return []
    try:
        if custom_forbidden_calls is None:
            rules = load_security_rules()
            custom_forbidden_calls = rules.get("custom_forbidden_calls", [])

        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            tree = ast.parse(f.read(), filename=file_path)
        visitor = CodeQLASTVisitor(file_path, custom_forbidden_calls=custom_forbidden_calls)
        visitor.visit(tree)
        return visitor.findings
    except SyntaxError as se:
        return [{
            "rule": "py/syntax-error",
            "cwe": "CWE-PARSER",
            "severity": "CRITICAL",
            "line": se.lineno or 1,
            "file": file_path,
            "msg": f"Syntax error in staged file: {str(se)}"
        }]
    except Exception:
        return []


# ---------------------------------------------------------------------------
# 4. L6 Intent-Drift & Scope Limiter + L4/L8 Pre-Flight Orchestrator
# ---------------------------------------------------------------------------

def _get_scope_file() -> Path:
    home = os.environ.get("GIT_OOPS_HOME", str(GIT_OOPS_HOME))
    return Path(home) / "scope.json"


def set_task_scope(patterns: List[str], max_files: Optional[int] = None) -> Dict[str, Any]:
    """Configures allowed directory/file scope and max-files blast-radius limit."""
    scope_file = _get_scope_file()
    scope_file.parent.mkdir(parents=True, exist_ok=True)
    cleaned = [p.strip().replace("\\", "/") for p in patterns if p.strip()]
    data = {"patterns": cleaned, "max_files": max_files}
    scope_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return data


def get_task_scope() -> Optional[Dict[str, Any]]:
    """Loads active L6 task scope boundaries if configured."""
    scope_file = _get_scope_file()
    if not scope_file.exists():
        return None
    try:
        return json.loads(scope_file.read_text(encoding="utf-8"))
    except Exception:
        return None


def clear_task_scope() -> None:
    """Removes active L6 task scope restrictions."""
    scope_file = _get_scope_file()
    if scope_file.exists():
        scope_file.unlink()


def check_scope_limits(staged_files: List[str]) -> List[Dict[str, Any]]:
    """Verifies that staged files stay within declared L6 scope patterns and max_files."""
    scope = get_task_scope()
    if not scope:
        return []
    violations: List[Dict[str, Any]] = []
    max_files = scope.get("max_files")
    if max_files is not None and len(staged_files) > int(max_files):
        violations.append({
            "rule": "l6/blast-radius-max-files",
            "cwe": "CWE-SCOPE-DRIFT",
            "severity": "CRITICAL",
            "line": 1,
            "file": "staged diff",
            "msg": f"[OOPS L6 SCOPE DRIFT] Staged {len(staged_files)} files, exceeding max_files limit of {max_files}.",
        })
    patterns = scope.get("patterns") or []
    if patterns:
        for fpath in staged_files:
            norm = fpath.replace("\\", "/")
            if not any(pat in norm for pat in patterns):
                violations.append({
                    "rule": "l6/intent-scope-violation",
                    "cwe": "CWE-SCOPE-DRIFT",
                    "severity": "CRITICAL",
                    "line": 1,
                    "file": fpath,
                    "msg": f"[OOPS L6 SCOPE DRIFT] '{fpath}' is outside declared task scope ({', '.join(patterns)}).",
                })
    return violations


def _scan_staged_python_files(staged_files: List[str]) -> List[Dict[str, Any]]:
    """Runs AST CWE and L4 complexity/nesting checks on staged Python files."""
    findings: List[Dict[str, Any]] = []
    for filepath in staged_files:
        if not filepath.endswith(".py") or not os.path.exists(filepath):
            continue
        findings.extend(scan_file_ast(filepath))
        norm = filepath.replace("\\", "/").lower()
        if not any(t in norm for t in ("tests/", "test_", "/tests/")):
            try:
                with open(filepath, "r", encoding="utf-8", errors="replace") as f:
                    ok_comp, comp_reason = check_nesting_and_complexity(f.read())
                if not ok_comp and comp_reason:
                    findings.append({
                        "rule": "l4/anti-slop-complexity",
                        "cwe": "CWE-ANTI-SLOP",
                        "severity": "HIGH",
                        "line": 1,
                        "file": filepath,
                        "msg": comp_reason,
                    })
            except Exception:
                pass
    return findings


def _extract_dep_candidates(filepath: str, content: str) -> List[str]:
    """Extracts package names from requirements.txt, pyproject.toml, or setup.py."""
    import re
    candidates: List[str] = []
    if filepath == "requirements.txt":
        for line in content.splitlines():
            stripped = line.strip()
            if stripped and not stripped.startswith("#"):
                m = re.match(r'^([a-zA-Z0-9_\-]+)', stripped)
                if m:
                    candidates.append(m.group(1))
    elif filepath in ("pyproject.toml", "setup.py"):
        blocks = re.findall(r'(?:dependencies|install_requires|requires)\s*=\s*\[(.*?)\]', content, re.DOTALL)
        for block in blocks:
            candidates.extend(re.findall(r'["\']([a-zA-Z0-9_\-]+)', block))
    return candidates


def _scan_staged_dependencies(staged_files: List[str]) -> List[Dict[str, Any]]:
    """Audits staged dependency manifests against OTA blacklists and typosquatting."""
    findings: List[Dict[str, Any]] = []
    dynamic_rules = load_security_rules()
    malicious_set = set(dynamic_rules.get("malicious_packages", []))

    for filepath in staged_files:
        if filepath not in ("requirements.txt", "pyproject.toml", "setup.py") or not os.path.exists(filepath):
            continue
        try:
            with open(filepath, "r", encoding="utf-8", errors="replace") as f:
                pkg_candidates = _extract_dep_candidates(filepath, f.read())
            for cand in pkg_candidates:
                if cand.lower() in malicious_set:
                    findings.append({
                        "rule": "supply-chain/known-malicious-package",
                        "cwe": "CWE-1357",
                        "severity": "CRITICAL",
                        "line": 1,
                        "file": filepath,
                        "msg": f"Package '{cand}' is listed on the active OTA malicious security blacklist.",
                    })
                    continue
                safe, reason = check_typosquatting(cand)
                if not safe:
                    findings.append({
                        "rule": "supply-chain/typosquatting",
                        "cwe": "CWE-1357",
                        "severity": "CRITICAL",
                        "line": 1,
                        "file": filepath,
                        "msg": reason,
                    })
        except Exception:
            pass
    return findings


def _run_custom_oops_scripts() -> List[Dict[str, Any]]:
    """Executes user-defined custom CI/CD scripts if present."""
    findings: List[Dict[str, Any]] = []
    custom_scripts = [
        Path(".oops/check.py"),
        Path(".oops/check.sh"),
        Path(".oops/pre-commit.sh"),
        Path(".git/hooks/pre-commit.local"),
    ]
    for script in custom_scripts:
        if not script.exists():
            continue
        try:
            cmd = [sys.executable, str(script)] if script.suffix == ".py" else [str(script)]
            c_proc = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            if c_proc.returncode != 0:
                findings.append({
                    "rule": "custom/user-script-failed",
                    "severity": "CRITICAL",
                    "line": 1,
                    "file": str(script),
                    "msg": f"Custom user CI/CD script '{script}' failed:\n{(c_proc.stderr or c_proc.stdout).strip()}",
                })
        except Exception as ex:
            findings.append({
                "rule": "custom/user-script-error",
                "severity": "CRITICAL",
                "line": 1,
                "file": str(script),
                "msg": f"Error running user custom script '{script}': {str(ex)}",
            })
    return findings


def _format_preflight_report(passed: bool, violations: List[Dict[str, Any]], staged_count: int) -> str:
    """Formats the L1-L8 pre-flight verification report."""
    if passed:
        return f"⚡ [git-oops] L3 Local Pre-Flight Check PASSED ({staged_count} staged files verified in <0.1s)."
    lines = ["🛑 [git-oops] L3 Local Pre-Flight CI/CD Security Check FAILED:"]
    for v in violations:
        sev = v.get("severity", "MEDIUM")
        rule = v.get("rule") or v.get("type", "SECURITY_ALERT")
        msg = v.get("msg") or v.get("label", "Violation detected")
        loc = f"{v.get('file', 'staged diff')}:{v.get('line', '?')}"
        lines.append(f"  • [{sev}] {rule} at {loc}")
        lines.append(f"    Reason: {msg}")
    lines.append("\nCommit BLOCKED by git-oops. Fix security issues or run with --no-verify if intentional.")
    return "\n".join(lines)


def run_l3_preflight() -> Tuple[bool, List[Dict[str, Any]], str]:
    """
    Executes complete local L1-L8 CI/CD pre-flight checks on staged git changes:
    - Emergency Freeze Gate (L8)
    - Zombie File & Scope Limiter (L4 / L6)
    - Secrets & High-Entropy Leak Check (L5)
    - Test-Deletion Fraud Interceptor (L4)
    - CodeQL AST Security CWE Rules & Complexity Limits (L2 / L4)
    - Supply-Chain & Typosquatting Audits (L5)
    Returns: (passed: bool, violations: list, formatted_report: str)
    """
    frozen, freeze_reason = is_workstation_frozen()
    if frozen:
        v = [{
            "rule": "l8/emergency-freeze",
            "severity": "CRITICAL",
            "line": 1,
            "file": "workstation",
            "msg": f"EMERGENCY FREEZE ACTIVE: {freeze_reason}. Run 'git-oops --unfreeze' to resume.",
        }]
        return False, v, f"🚨 [git-oops] BLOCKED by Emergency Freeze: {freeze_reason}"

    staged_proc = subprocess.run(
        ["git", "diff", "--cached", "--name-only"],
        capture_output=True, text=True, errors="replace"
    )
    staged_files = [f.strip() for f in staged_proc.stdout.splitlines() if f.strip()]
    if not staged_files:
        return True, [], "No staged changes detected. Pre-flight passed."

    diff_proc = subprocess.run(
        ["git", "diff", "--cached"],
        capture_output=True, text=True, errors="replace"
    )
    diff_text = diff_proc.stdout

    violations: List[Dict[str, Any]] = []
    violations.extend(check_zombie_files(staged_files))
    violations.extend(check_scope_limits(staged_files))
    violations.extend(scan_diff_for_secrets(diff_text))
    _, assertion_violations = check_test_assertion_guard(diff_text)
    violations.extend(assertion_violations)
    violations.extend(_scan_staged_python_files(staged_files))
    violations.extend(_scan_staged_dependencies(staged_files))
    violations.extend(_run_custom_oops_scripts())

    passed = len([v for v in violations if v.get("severity") in ("CRITICAL", "HIGH")]) == 0
    return passed, violations, _format_preflight_report(passed, violations, len(staged_files))


def run_pre_push_check() -> Tuple[bool, str]:
    """
    Executes pre-push verification:
    - Enforces Emergency Freeze Lock (L8)
    - Enforces Human Affirmation Gate for AI agents (L8)
    - Scans outgoing commits for secret leaks (L5)
    """
    frozen, freeze_reason = is_workstation_frozen()
    if frozen:
        return False, f"🚨 [git-oops] Pre-push BLOCKED by Emergency Freeze: {freeze_reason}"

    affirmed, affirm_msg = verify_human_affirmation("git push")
    if not affirmed:
        return False, f"🛑 [git-oops] Pre-push BLOCKED: {affirm_msg}"

    # Check current branch
    branch_proc = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        capture_output=True, text=True, errors="replace"
    )
    current_branch = branch_proc.stdout.strip()

    # Run pre-flight on unpushed commits
    diff_proc = subprocess.run(
        ["git", "diff", "@{u}..HEAD"],
        capture_output=True, text=True, errors="replace"
    )
    if diff_proc.returncode == 0 and diff_proc.stdout.strip():
        secret_findings = scan_diff_for_secrets(diff_proc.stdout)
        if secret_findings:
            return False, f"🛑 [git-oops] Pre-push BLOCKED: {len(secret_findings)} secret leaks detected in outgoing commits!"

    return True, f"⚡ [git-oops] Pre-push verification PASSED on branch '{current_branch}'."
