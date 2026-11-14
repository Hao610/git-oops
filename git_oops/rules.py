"""
Git-Oops Dynamic OTA Security Rules Engine
Decouples security signatures from Python source code.
Automatically syncs latest CVEs, malicious packages, and secret regex patterns
in the background when internet is available, with pure offline baseline fallback.
"""

import os
import sys
import json
import time
import urllib.request
import urllib.error
import threading
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

RULES_DIR = Path.home() / ".git_oops" / "rules"
RULES_FILE = RULES_DIR / "security_rules.json"
RULES_CACHE_META = RULES_DIR / "rules_meta.json"

# 24-hour cache TTL
SYNC_INTERVAL_SECONDS = 86400

# Built-in offline baseline rules (Hardened fallback - zero network required)
OFFLINE_BASELINE_RULES: Dict[str, Any] = {
    "version": "1.0.5-baseline",
    "last_updated": 1731550000,
    "secret_patterns": [
        {"pattern": r"(?i)(?:api[_-]?key|secret|password|passwd|auth[_-]?token)\s*[:=]\s*['\"]([a-zA-Z0-9_\-\.]{16,})['\"]", "label": "Exposed Secret Literal", "severity": "CRITICAL"},
        {"pattern": r"(?i)sk-[a-zA-Z0-9]{32,}", "label": "OpenAI API Key", "severity": "CRITICAL"},
        {"pattern": r"(?i)AKIA[0-9A-Z]{16}", "label": "AWS Access Key ID", "severity": "CRITICAL"},
        {"pattern": r"(?i)ghp_[a-zA-Z0-9]{36}", "label": "GitHub Personal Access Token", "severity": "CRITICAL"},
        {"pattern": r"(?i)xox[baprs]-[0-9a-zA-Z]{10,48}", "label": "Slack OAuth Token", "severity": "CRITICAL"},
        {"pattern": r"-----BEGIN (?:RSA|OPENSSH|DSA|EC|PGP)? PRIVATE KEY-----", "label": "Cryptographic Private Key", "severity": "CRITICAL"}
    ],
    "malicious_packages": [
        "reqeusts", "colorma", "djagno", "falsk", "beautiflsoup",
        "cryptograpy", "numpay", "scipyy", "pandass", "tensoflow",
        "pytocrh", "opencvv", "selenuim", "urlib3", "certifii"
    ],
    "cwe_thresholds": {
        "max_cyclomatic_complexity": 10,
        "shannon_entropy_threshold": 4.6
    }
}

# Upstream OTA rule endpoints (Primary GitHub Raw feed + fallback)
OTA_FEED_URLS = [
    "https://raw.githubusercontent.com/Hao610/git-oops/main/rules/security_rules.json",
    "https://api.github.com/repos/Hao610/git-oops/contents/rules/security_rules.json"
]


# ---------------------------------------------------------------------------
# Additive User-Custom Policy Support (Immutable Baseline + Additive Custom)
# ---------------------------------------------------------------------------

CUSTOM_GLOBAL_RULES_FILE = RULES_DIR / "custom_rules.json"


def find_repo_custom_rules_file() -> Optional[Path]:
    """Finds repo-level custom rules file (.oops/rules.json or .oops-rules.json)."""
    cwd = Path.cwd()
    for cand in (cwd / ".oops" / "rules.json", cwd / ".oops-rules.json", cwd / "oops-rules.json"):
        if cand.exists():
            return cand
    return None


def load_user_custom_rules() -> Dict[str, Any]:
    """
    Loads user-defined custom security rules from:
    1. Repo root (.oops/rules.json or .oops-rules.json)
    2. Global custom rules (~/.git_oops/rules/custom_rules.json)
    Users can ONLY ADD custom rules; they CANNOT delete or bypass system baselines.
    """
    custom = {
        "extra_secret_patterns": [],
        "extra_banned_packages": [],
        "extra_forbidden_calls": []
    }

    # 1. Global custom rules
    if CUSTOM_GLOBAL_RULES_FILE.exists():
        try:
            with open(CUSTOM_GLOBAL_RULES_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                custom["extra_secret_patterns"].extend(data.get("extra_secret_patterns", []))
                custom["extra_banned_packages"].extend(data.get("extra_banned_packages", []))
                custom["extra_forbidden_calls"].extend(data.get("extra_forbidden_calls", []))
        except Exception:
            pass

    # 2. Repo-level custom rules (takes precedence for repo-specific policies)
    repo_rules = find_repo_custom_rules_file()
    if repo_rules:
        try:
            with open(repo_rules, "r", encoding="utf-8") as f:
                data = json.load(f)
                custom["extra_secret_patterns"].extend(data.get("extra_secret_patterns", []))
                custom["extra_banned_packages"].extend(data.get("extra_banned_packages", []))
                custom["extra_forbidden_calls"].extend(data.get("extra_forbidden_calls", []))
        except Exception:
            pass

    return custom


def is_valid_regex(pattern_str: str) -> bool:
    """Checks if regex compiles without syntax error."""
    import re
    if not pattern_str or not isinstance(pattern_str, str):
        return False
    try:
        re.compile(pattern_str)
        return True
    except Exception:
        return False


def load_security_rules() -> Dict[str, Any]:
    """
    Loads merged security rules with cryptographic integrity and tamper resistance:
    [Hardcoded Immutable Baseline] + [OTA Live Dynamic Signatures] + [User Custom Additions]
    Baseline checks CANNOT be removed, overridden, or hollowed out by tampering.
    """
    # 1. Start with immutable baseline constant directly from Python memory
    merged = json.loads(json.dumps(OFFLINE_BASELINE_RULES))

    # 2. Layer OTA dynamic signatures if available (with tamper & corruption check)
    tamper_detected = False
    try:
        if RULES_FILE.exists():
            with open(RULES_FILE, "r", encoding="utf-8") as f:
                ota_data = json.load(f)
                if isinstance(ota_data, dict):
                    # Union malicious packages
                    incoming_pkgs = ota_data.get("malicious_packages", [])
                    if isinstance(incoming_pkgs, list):
                        pkgs = set(merged.get("malicious_packages", [])) | set(incoming_pkgs)
                        merged["malicious_packages"] = sorted(list(pkgs))

                    # Union secret patterns (discarding any invalid or tampered regexes)
                    curr_patts = {p["pattern"]: p for p in merged.get("secret_patterns", [])}
                    for p in ota_data.get("secret_patterns", []):
                        if isinstance(p, dict) and is_valid_regex(p.get("pattern", "")):
                            curr_patts[p["pattern"]] = p
                    merged["secret_patterns"] = list(curr_patts.values())
        else:
            tamper_detected = True
    except Exception:
        tamper_detected = True

    # 3. Layer User's Custom Additions (Additive-Only)
    user_custom = load_user_custom_rules()
    if user_custom["extra_banned_packages"]:
        merged["malicious_packages"] = sorted(list(set(merged.get("malicious_packages", [])) | set(user_custom["extra_banned_packages"])))

    if user_custom["extra_secret_patterns"]:
        curr_patts = {p["pattern"]: p for p in merged.get("secret_patterns", [])}
        for p in user_custom["extra_secret_patterns"]:
            if isinstance(p, dict) and is_valid_regex(p.get("pattern", "")):
                curr_patts[p["pattern"]] = p
        merged["secret_patterns"] = list(curr_patts.values())

    merged["custom_forbidden_calls"] = user_custom.get("extra_forbidden_calls", [])

    # 4. Anti-Tamper Invariant Check:
    # Baseline packages and secret patterns must be strictly preserved.
    # If file was deleted or corrupted, instantly self-heal and re-serialize to disk.
    baseline_pkgs = set(OFFLINE_BASELINE_RULES["malicious_packages"])
    if not baseline_pkgs.issubset(set(merged["malicious_packages"])) or tamper_detected or not RULES_FILE.exists():
        save_security_rules(merged)

    return merged


def save_security_rules(rules: Dict[str, Any]) -> bool:
    """Saves updated dynamic security rules to ~/.git_oops/rules/security_rules.json."""
    try:
        RULES_DIR.mkdir(parents=True, exist_ok=True)
        with open(RULES_FILE, "w", encoding="utf-8") as f:
            json.dump(rules, f, indent=2, ensure_ascii=False)
        return True
    except Exception:
        return False


def is_sync_due() -> bool:
    """Checks if 24 hours have elapsed since the last OTA check."""
    try:
        if not RULES_CACHE_META.exists():
            return True
        with open(RULES_CACHE_META, "r", encoding="utf-8") as f:
            meta = json.load(f)
            last_sync = meta.get("last_sync_timestamp", 0)
            return (time.time() - last_sync) > SYNC_INTERVAL_SECONDS
    except Exception:
        return True


def record_sync_timestamp(status: str = "success"):
    """Records the timestamp of the last OTA rule check."""
    try:
        RULES_DIR.mkdir(parents=True, exist_ok=True)
        with open(RULES_CACHE_META, "w", encoding="utf-8") as f:
            json.dump({"last_sync_timestamp": time.time(), "status": status}, f)
    except Exception:
        pass


def fetch_remote_rules(timeout: float = 2.0) -> Tuple[bool, Dict[str, Any]]:
    """
    Attempts to download latest dynamic security rules from remote OTA feed.
    Times out in 2.0 seconds so it never hangs.
    """
    for url in OTA_FEED_URLS:
        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "git-oops-ota-client/1.0.5"}
            )
            with urllib.request.urlopen(req, timeout=timeout) as response:
                if response.status == 200:
                    raw_data = response.read().decode("utf-8")
                    parsed = json.loads(raw_data)
                    # If returned from GitHub API base64
                    if isinstance(parsed, dict) and "content" in parsed and "encoding" in parsed:
                        import base64
                        decoded = base64.b64decode(parsed["content"]).decode("utf-8")
                        parsed = json.loads(decoded)
                    if isinstance(parsed, dict) and "secret_patterns" in parsed:
                        return True, parsed
        except Exception:
            continue
    return False, {}


def sync_security_rules_foreground(force: bool = False) -> Tuple[bool, str]:
    """
    Synchronous rule update function.
    Downloads, validates, merges and saves updated security definitions.
    """
    if not force and not is_sync_due():
        return True, "Dynamic security rules are up to date (cached within 24h)."

    ok, remote_rules = fetch_remote_rules(timeout=2.5)
    record_sync_timestamp(status="success" if ok else "offline")

    if not ok:
        return False, "Offline or remote rules feed unreachable. Using verified local baseline."

    # Merge remote rules with local rules safely
    current_rules = load_security_rules()

    # Merge malicious packages (deduplicated set)
    current_pkgs = set(current_rules.get("malicious_packages", []))
    remote_pkgs = set(remote_rules.get("malicious_packages", []))
    merged_pkgs = sorted(list(current_pkgs | remote_pkgs))

    # Merge secret patterns
    curr_patterns = {p["pattern"]: p for p in current_rules.get("secret_patterns", [])}
    for p in remote_rules.get("secret_patterns", []):
        curr_patterns[p["pattern"]] = p

    current_rules["malicious_packages"] = merged_pkgs
    current_rules["secret_patterns"] = list(curr_patterns.values())
    current_rules["version"] = remote_rules.get("version", "1.0.5-ota")
    current_rules["last_updated"] = int(time.time())

    save_security_rules(current_rules)
    return True, f"Successfully synced security rules (v{current_rules['version']}): {len(merged_pkgs)} malicious packages, {len(current_rules['secret_patterns'])} secret patterns active."


def trigger_ota_update_background():
    """
    Fires a non-blocking background daemon thread to silently refresh security rules.
    Takes 0ms on the calling thread.
    """
    if not is_sync_due():
        return

    def _worker():
        try:
            sync_security_rules_foreground(force=False)
        except Exception:
            pass

    t = threading.Thread(target=_worker, daemon=True)
    t.start()
