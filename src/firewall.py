"""
Git-Oops Agent Shield: Blast-Radius Firewall & Malicious Package Guard
Blocks destructive terminal commands and hallucinated package installations.
"""

import os
import re
import shlex
import secrets
from typing import Tuple, Optional, Callable

from src.watchdog import is_workstation_frozen

AGENT_ENV_VARS = (
    "ANTIGRAVITY_AGENT_ID",
    "CLAUDE_CODE",
    "CURSOR_TRACE",
    "AIDER",
    "DEVIN",
    "GIT_OOPS_AGENT_MODE",
    "MCP_SESSION",
)

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


def detect_agent_context() -> Optional[str]:
    """Detects whether the current process is executing inside an autonomous AI agent environment."""
    for env_var in AGENT_ENV_VARS:
        val = os.environ.get(env_var)
        if val and val.strip() not in ("0", "false", "False"):
            return env_var
    return None


def _tokenize_command(command: str) -> list:
    """Safely tokenizes a shell command using shlex lexical decomposition."""
    try:
        return shlex.split(command)
    except ValueError:
        return command.split()


def _has_pipe_to_shell(command: str) -> bool:
    """Uses shlex-aware segment inspection to detect curl/wget piped to sh/bash/python."""
    if "|" not in command:
        return False
    segments = [seg.strip() for seg in command.split("|")]
    downloaders = {"curl", "wget", "fetch", "iwr", "invoke-webrequest"}
    shells = {"sh", "bash", "zsh", "dash", "pwsh", "powershell", "python", "python3"}
    has_downloader = False
    for seg in segments:
        tokens = _tokenize_command(seg)
        if not tokens:
            continue
        base_cmd = os.path.basename(tokens[0]).lower()
        if base_cmd in downloaders:
            has_downloader = True
        elif has_downloader and base_cmd in shells:
            return True
    return False


def requires_human_affirmation(command: str) -> bool:
    """Returns True if the command performs a sensitive remote push, release tag, or branch deletion."""
    tokens = _tokenize_command(command.strip())
    if len(tokens) < 2 or os.path.basename(tokens[0]).lower() != "git":
        return False
    subcmd = tokens[1].lower()
    if subcmd in ("push", "tag"):
        return True
    if subcmd == "branch" and any(flag in tokens[2:] for flag in ("-D", "-d", "--delete")):
        return True
    return False


def generate_affirmation_token() -> str:
    """Generates an ephemeral 4-character cryptographic confirmation token."""
    return secrets.token_hex(2).upper()


def _read_physical_tty(prompt: str) -> Optional[str]:
    """Reads directly from the physical TTY device, rejecting piped stdin."""
    import sys
    sys.stderr.write(prompt)
    sys.stderr.flush()
    tty_path = "CONIN$" if os.name == "nt" else "/dev/tty"
    try:
        with open(tty_path, "r", encoding="utf-8", errors="replace") as tty:
            return tty.readline().strip()
    except OSError:
        return None


def verify_human_affirmation(
    command: str,
    tty_reader: Optional[Callable[[str], Optional[str]]] = None,
) -> Tuple[bool, str]:
    """
    L8 Human Affirmation Gate:
    If invoked inside an AI agent context for sensitive git mutations, requires
    the physical operator to enter an ephemeral confirmation token via TTY.
    """
    agent_id = detect_agent_context()
    if not agent_id or not requires_human_affirmation(command):
        return True, "AFFIRMED"

    token = generate_affirmation_token()
    prompt = (
        f"\n[OOPS-GATE] Agent context '{agent_id}' attempted: {command}\n"
        f"[OOPS-GATE] Physical operator must enter confirmation token '{token}' to proceed: "
    )
    reader = tty_reader or _read_physical_tty
    entered = reader(prompt)
    if entered is None:
        return False, (
            f"HUMAN_AFFIRMATION_DENIED: No physical TTY available to confirm '{command}' "
            f"from agent '{agent_id}'."
        )
    if entered.strip().upper() != token:
        return False, (
            f"HUMAN_AFFIRMATION_DENIED: Invalid confirmation token for '{command}'."
        )
    return True, "AFFIRMED"


def check_command_safety(command: str) -> Tuple[bool, Optional[str]]:
    """
    Evaluates whether a command proposed by an Agent breaches the blast-radius firewall.
    Returns (True, None) if safe, or (False, reason) if blocked.
    """
    frozen, freeze_reason = is_workstation_frozen()
    if frozen:
        return False, f"EMERGENCY_FREEZE_BLOCKED: {freeze_reason}"

    cmd = command.strip()
    if _has_pipe_to_shell(cmd):
        return False, "EXECUTION_FIREWALL_BLOCKED: Piped remote script execution (downloader | shell) detected via shlex."

    for pattern, reason in BLOCKED_COMMAND_PATTERNS:
        if re.search(pattern, cmd, re.IGNORECASE):
            return False, f"FIREWALL_BLOCKED: {reason} (matched pattern: {pattern})"

    # Check for hallucinated / typosquatted package installs
    if "pip install" in cmd.lower() or "npm install" in cmd.lower():
        for bad_pkg in SUSPICIOUS_PACKAGE_PATTERNS:
            if re.search(rf"\b{bad_pkg}\b", cmd, re.IGNORECASE):
                return False, f"SUPPLY_CHAIN_BLOCKED: Known hallucinated or typosquatted package trap detected ('{bad_pkg}')."

    return True, None
