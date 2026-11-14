"""
Git-Oops Agent Shield: Blast-Radius Firewall & Malicious Package Guard
Blocks destructive terminal commands and hallucinated package installations.
"""

import re
from typing import Tuple, Optional

# Disastrous command signatures that agents must never execute
BLOCKED_COMMAND_PATTERNS = [
    (r"\brm\s+-[rRfF]*\s+[/~*]", "Destructive root/home/wildcard filesystem deletion"),
    (r"\brmdir\s+/[sS]\s+/[qQ]", "Windows destructive root deletion"),
    (r"\bdel\s+/[fF]\s+/[sS]\s+/[qQ]\s+[*A-Za-z]:", "Windows full drive wiping"),
    (r"\bgit\s+reset\s+--hard\s+HEAD~[5-9]|\bgit\s+reset\s+--hard\s+[a-f0-9]{7,}", "Deep irreversible commit history wipe"),
    (r"\bgit\s+push\s+.*--force.*origin\s+(main|master)", "Destructive remote production branch force-push"),
    (r"\b(format|diskpart|mkfs)\b", "Disk formatting partition destruction"),
    (r"\bdd\s+if=.*of=/dev/", "Raw device destruction"),
    (r":\(\)\s*\{\s*:\s*\|\s*:\s*&\s*\}\s*;\s*:", "Fork bomb terminal crash"),
    (r"\b(chmod|chown)\s+-R\s+777\s+[/~]", "Catastrophic global permission compromise")
]

# Well-known hallucinated or typosquatted AI package traps
SUSPICIOUS_PACKAGE_PATTERNS = [
    r"reqeusts",
    r"colorama-v2",
    r"python-date-util",
    r"crypto-js-node",
    r"torch-gpu-fast"
]


def check_command_safety(command: str) -> Tuple[bool, Optional[str]]:
    """
    Evaluates whether a command proposed by an Agent breaches the blast-radius firewall.
    Returns (True, None) if safe, or (False, reason) if blocked.
    """
    cmd = command.strip()
    for pattern, reason in BLOCKED_COMMAND_PATTERNS:
        if re.search(pattern, cmd, re.IGNORECASE):
            return False, f"FIREWALL_BLOCKED: {reason} (matched pattern: {pattern})"

    # Check for hallucinated / typosquatted package installs
    if "pip install" in cmd.lower() or "npm install" in cmd.lower():
        for bad_pkg in SUSPICIOUS_PACKAGE_PATTERNS:
            if re.search(rf"\b{bad_pkg}\b", cmd, re.IGNORECASE):
                return False, f"SUPPLY_CHAIN_BLOCKED: Known hallucinated or typosquatted package trap detected ('{bad_pkg}')."

    return True, None
