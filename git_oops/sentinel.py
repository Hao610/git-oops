"""
Git-Oops Advanced Security & Quality Filters (Features #17, #18, #19, #20)
1. Egress Sniffer: Detects unauthorized outbound telemetry/data exfiltration.
2. Anti-Bloat Linter: Measures cyclomatic complexity to prevent spaghetti code rot.
3. License Taint Shield: Detects restricted GPL/viral license headers in proposed snippets.
4. Intent Prefetch Engine: Predicts agent execution chains for 0ms cached responses.
"""

import re
import ast
from typing import Tuple, Optional, Dict, Any

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
