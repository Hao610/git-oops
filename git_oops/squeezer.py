"""
Git-Oops Squeezer: Token-Density Context Compressor & Secret Redactor
Turns 5,000-line noisy stack dumps into a pristine 20-line payload for Agents.
Redacts all private tokens, API keys, and environment passwords.
"""

import re

# High-entropy secret patterns
SECRET_PATTERNS = [
    (r"(?i)(api[_-]?key|secret|token|password|bearer|auth|access_key)[\s:=\"']+([A-Za-z0-9_\-\.\/]{12,})", r"\1='<REDACTED_SECRET>'"),
    (r"AIzaSy[A-Za-z0-9_\-]{33}", "<REDACTED_GEMINI_KEY>"),
    (r"sk-[A-Za-z0-9]{32,}", "<REDACTED_OPENAI_KEY>"),
    (r"ghp_[A-Za-z0-9]{36}", "<REDACTED_GITHUB_TOKEN>"),
    (r"AKIA[0-9A-Z]{16}", "<REDACTED_AWS_KEY>")
]

# Patterns of noisy, low-value terminal junk
NOISY_PATTERNS = [
    r"^\s*at\s+async\s+.*\bnode_modules\b.*$",
    r"^\s*at\s+.*node:internal.*$",
    r"^.*npm\s+http\s+200.*$",
    r"^.*Downloading\s+.*\b\d+%.*$",
    r"^\s*\.+\s*$",
    r"^.*pytest-cache.*$",
    r"^\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])"  # ANSI color codes
]


def redact_secrets(raw_text: str) -> str:
    """Masks credentials, bearer tokens, and keys before text reaches any AI model."""
    result = raw_text
    for pattern, replacement in SECRET_PATTERNS:
        result = re.sub(pattern, replacement, result)
    return result


def compress_traceback(raw_logs: str, max_lines: int = 25) -> str:
    """
    Strips ANSI noise, internal runtime plumbing, and preserves the pivotal
    Leaf Frame, exception name, and local variables.
    """
    clean_text = redact_secrets(raw_logs)
    lines = clean_text.splitlines()

    filtered = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        # Skip repetitive node_modules / runtime spam
        if any(re.search(np, stripped) for np in NOISY_PATTERNS):
            continue
        filtered.append(line)

    if len(filtered) <= max_lines:
        return "\n".join(filtered)

    # Focus on the beginning (command setup) and crucial tail (root exception and frames)
    head = filtered[:5]
    tail = filtered[-(max_lines - 7):]
    omitted = len(filtered) - len(head) - len(tail)
    summary = head + [f"    ... [{omitted} lines of internal runtime frames compressed by git-oops] ..."] + tail
    return "\n".join(summary)
