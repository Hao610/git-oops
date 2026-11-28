"""
Git-Oops Advanced Security & Quality Filters (Features #17, #18, #19, #20)
1. Egress Sniffer: Detects unauthorized outbound telemetry/data exfiltration.
2. Anti-Bloat Linter: Measures cyclomatic complexity to prevent spaghetti code rot.
3. License Taint Shield: Detects restricted GPL/viral license headers in proposed snippets.
4. Intent Prefetch Engine: Predicts agent execution chains for 0ms cached responses.
"""

import os
import re
import ast
from typing import Tuple, Optional, Dict, Any, List

# Unauthorized remote telemetry endpoints and exfiltration patterns
EGRESS_PATTERNS = [
    r"(?i)https?://[a-zA-Z0-9\-\.]*(webhook|evil|pastebin|ngrok|pipedream|requestbin)",
    r"(?i)socket\.connect\(",
    r"(?i)urllib\.request\.urlopen\(",
    r"(?i)requests\.(post|put)\(.*(api_key|token|password|environ)"
]

# Viral license contamination indicators
LICENSE_TAINT_PATTERNS = [
    r"GNU GENERAL PUBLIC LICENSE",
    r"Affero General Public License",
    r"GPL-3\.0",
    r"AGPL-3\.0",
    r"All rights reserved.*Confidential"
]


def check_egress_security(code_snippet: str) -> Tuple[bool, Optional[str]]:
    """Inspects patch snippet for hidden phone-home or credential exfiltration attempts."""
    for pattern in EGRESS_PATTERNS:
        if re.search(pattern, code_snippet):
            return False, f"EGRESS_ALERT: Potential unauthorized outbound network call detected (matched pattern: {pattern})."
    return True, None


def check_license_taint(code_snippet: str) -> Tuple[bool, Optional[str]]:
    """Guards codebase against viral GPL/AGPL or proprietary copyright contamination."""
    for pattern in LICENSE_TAINT_PATTERNS:
        if re.search(pattern, code_snippet, re.IGNORECASE):
            return False, f"LICENSE_TAINT_BLOCKED: Viral or restricted license header detected ('{pattern}'). Must be original MIT/Apache-2.0 code."
    return True, None


def check_code_complexity(python_code: str, max_allowed_complexity: int = 10) -> Tuple[bool, Optional[str]]:
    """
    Measures cyclomatic complexity using AST nodes (branches, loops, try/except).
    Rejects patches that introduce unnecessary AI-spaghetti code bloat.
    """
    try:
        tree = ast.parse(python_code)
    except Exception:
        return True, None  # Allow non-python or partial diff chunks

    complexity = 1
    for node in ast.walk(tree):
        if isinstance(node, (ast.If, ast.While, ast.For, ast.ExceptHandler, ast.With, ast.Assert)):
            complexity += 1
        elif isinstance(node, ast.BoolOp):
            complexity += len(node.values) - 1

    if complexity > max_allowed_complexity:
        return False, f"ANTI_BLOAT_VIOLATION: Complexity is {complexity} (limit: {max_allowed_complexity}). Simplify nested logic; avoid AI spaghetti code."
    return True, None


_TEST_FILE_MARKERS = ("tests/", "test_", "/tests/", "spec/", "__tests__/")
_ASSERTION_REGEX = re.compile(r"\b(?:assert|expect|self\.assert\w*)\b")
_SKIP_REGEX = re.compile(r"(?:@pytest\.mark\.skip|@unittest\.skip|\bit\.skip\b|\btest\.skip\b)")
_ZOMBIE_PATTERNS = (
    re.compile(r"^temp_fix", re.IGNORECASE),
    re.compile(r"_old\.[^.]+$", re.IGNORECASE),
    re.compile(r"_temp\.[^.]+$", re.IGNORECASE),
    re.compile(r"^scratch_", re.IGNORECASE),
    re.compile(r"^backup\.[^.]+$", re.IGNORECASE),
    re.compile(r"\.(bak|tmp)$", re.IGNORECASE),
)
_NESTING_NODES = (ast.If, ast.For, ast.AsyncFor, ast.While, ast.With, ast.AsyncWith, ast.Try)


def _is_test_file(filepath: str) -> bool:
    norm = filepath.replace("\\", "/").lower()
    return any(marker in norm for marker in _TEST_FILE_MARKERS)


def _collect_test_diff_stats(diff_text: str) -> Dict[str, Dict[str, int]]:
    """Collects added/removed assertion counts and injected skip markers per test file."""
    per_file_stats: Dict[str, Dict[str, int]] = {}
    current_file = ""
    for line in diff_text.splitlines():
        if line.startswith("+++ b/"):
            current_file = line[6:].strip()
            continue
        if not current_file or not _is_test_file(current_file):
            continue
        stats = per_file_stats.setdefault(current_file, {"added": 0, "removed": 0, "skips": 0})
        if line.startswith("+") and not line.startswith("+++"):
            content = line[1:]
            stats["added"] += 1 if _ASSERTION_REGEX.search(content) else 0
            stats["skips"] += 1 if _SKIP_REGEX.search(content) else 0
        elif line.startswith("-") and not line.startswith("---") and _ASSERTION_REGEX.search(line[1:]):
            stats["removed"] += 1
    return per_file_stats


def check_test_assertion_guard(diff_text: str) -> Tuple[bool, List[Dict[str, Any]]]:
    """
    L4 Test-Deletion Fraud Interceptor:
    Detects net reduction of test assertions or newly injected skip markers in test files.
    """
    per_file_stats = _collect_test_diff_stats(diff_text)
    violations: List[Dict[str, Any]] = []
    for fpath, stats in per_file_stats.items():
        net_delta = stats["added"] - stats["removed"]
        if net_delta >= 0 and stats["skips"] == 0:
            continue
        reasons = []
        if net_delta < 0:
            reasons.append(f"Net assertion reduction ({net_delta} assertions)")
        if stats["skips"] > 0:
            reasons.append(f"{stats['skips']} test skip marker(s) injected")
        violations.append({
            "rule": "l4/test-deletion-fraud",
            "cwe": "CWE-ANTI-SLOP",
            "severity": "CRITICAL",
            "line": 1,
            "file": fpath,
            "msg": f"[OOPS L4 CHEAT DETECTED] {'; '.join(reasons)} in '{fpath}'. Agents may not delete or skip assertions to pass CI.",
        })
    return len(violations) == 0, violations


def _calc_func_metrics(func_node: ast.AST) -> Tuple[int, int, int]:
    """Computes (cyclomatic_complexity, max_nesting_depth, line_span) for an AST function."""
    complexity = 1
    for node in ast.walk(func_node):
        if isinstance(node, (ast.If, ast.While, ast.For, ast.AsyncFor, ast.ExceptHandler, ast.With, ast.AsyncWith, ast.Assert)):
            complexity += 1
        elif isinstance(node, ast.BoolOp):
            complexity += len(node.values) - 1

    def _max_depth(node: ast.AST, depth: int) -> int:
        best = depth
        for child in ast.iter_child_nodes(node):
            next_depth = depth + 1 if isinstance(child, _NESTING_NODES) else depth
            best = max(best, _max_depth(child, next_depth))
        return best

    nesting = _max_depth(func_node, 0)
    end_line = getattr(func_node, "end_lineno", None) or getattr(func_node, "lineno", 1)
    start_line = getattr(func_node, "lineno", 1)
    return complexity, nesting, max(1, end_line - start_line + 1)


def check_nesting_and_complexity(
    python_code: str,
    max_complexity: int = 12,
    max_nesting: int = 4,
    max_func_lines: int = 150,
) -> Tuple[bool, Optional[str]]:
    """
    L4 Cyclomatic Complexity & Nesting Gatekeeper:
    Inspects each function in python_code against McCabe complexity, nesting depth, and line length.
    """
    try:
        tree = ast.parse(python_code)
    except Exception:
        return True, None

    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        complexity, nesting, span = _calc_func_metrics(node)
        if complexity > max_complexity:
            return False, f"ANTI_BLOAT_VIOLATION: Function '{node.name}' complexity is {complexity} (limit: {max_complexity})."
        if nesting > max_nesting:
            return False, f"ANTI_BLOAT_VIOLATION: Function '{node.name}' nesting depth is {nesting} (limit: {max_nesting})."
        if span > max_func_lines:
            return False, f"ANTI_BLOAT_VIOLATION: Function '{node.name}' length is {span} lines (limit: {max_func_lines})."

    return True, None


def check_zombie_files(staged_files: List[str]) -> List[Dict[str, Any]]:
    """
    L4 Zombie File & Dead Code Sentinel:
    Flags scratch, temporary, or backup files staged for commit.
    """
    violations: List[Dict[str, Any]] = []
    for fpath in staged_files:
        basename = os.path.basename(fpath.strip())
        if any(pat.search(basename) for pat in _ZOMBIE_PATTERNS):
            violations.append({
                "rule": "l4/zombie-scratch-file",
                "cwe": "CWE-ANTI-SLOP",
                "severity": "HIGH",
                "line": 1,
                "file": fpath,
                "msg": f"[OOPS L4 ZOMBIE FILE] Temporary or backup scratch file '{fpath}' detected. Remove before committing.",
            })
    return violations


class IntentPrefetchEngine:
    """Predicts next probable command in the agent tool-chain to warm cache in background."""
    CHAIN_TRANSITIONS = {
        "apply_patch": "pytest",
        "crashed": "diagnose_and_patch",
        "pytest_failed": "squeezer"
    }

    @classmethod
    def predict_next_action(cls, current_action: str) -> str:
        return cls.CHAIN_TRANSITIONS.get(current_action, "idle")
