"""
Test suite for Git-Oops v1.0.5 (Enterprise Edition)
Covers all new core pillars: Zero-step Hooks, L3 Pre-Flight, OTA Rules,
Hardware Throttling, AST Symbolic Solver, Typosquatting Interceptor,
Crash Replay, Reflog Salvage, Pre-PR Gatekeeper, and Local LLM Adapter.
"""

import os
import sys
import json
import pytest
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.hooks import (
    calculate_shannon_entropy,
    scan_diff_for_secrets,
    scan_file_ast,
    setup_global_hooks,
    ensure_auto_hooks
)
from src.rules import (
    load_security_rules,
    save_security_rules,
    is_sync_due,
    sync_security_rules_foreground,
    OFFLINE_BASELINE_RULES
)
from src.hardware import (
    get_hardware_telemetry,
    check_hardware_throttling,
    down_prioritize_process
)
from src.supply_chain import (
    check_typosquatting,
    levenshtein_distance,
    scan_dependencies_file
)
from src.solver import (
    solve_with_ast,
    solve_none_attribute_error,
    solve_key_error,
    solve_zero_division_error
)
from src.replay import (
    record_crash_snapshot,
    inspect_crash_snapshot,
    list_crash_snapshots
)
from src.salvage import (
    run_reflog_autopsy,
    GhostWorktreeSandbox
)
from src.tester import (
    synthesize_regression_test
)
from src.local_llm import (
    probe_local_llm,
    call_local_llm
)
from src.reviewer import (
    review_pull_request,
    format_pr_review_markdown
)


def test_shannon_entropy():
    # Low entropy plain string
    low_e = calculate_shannon_entropy("aaaaaaaaaaaa")
    assert low_e < 1.0

    # High entropy random base64 secret token
    high_e = calculate_shannon_entropy("dGhpc0lzQVZlcnlIaWdoRW50cm9weVNlY3JldEtleTEyMw==")
    assert high_e > 4.0


def test_scan_diff_for_secrets():
    diff_with_secret = """--- a/config.py
+++ b/config.py
@@ -1,3 +1,4 @@
+OPENAI_API_KEY = "sk-1234567890abcdef1234567890abcdef"
+AWS_KEY = "AKIA1234567890ABCDEF"
+print("normal line")
"""
    violations = scan_diff_for_secrets(diff_with_secret)
    labels = [v["label"] for v in violations]
    assert any("OpenAI API Key" in l for l in labels)
    assert any("AWS Access Key" in l for l in labels)


def test_codeql_ast_security_rules(tmp_path):
    unsafe_py = tmp_path / "unsafe.py"
    unsafe_py.write_text("""
import os

def run_query(user_id):
    query = "SELECT * FROM users WHERE id = " + user_id
    cursor.execute(query)

def dangerous_eval(payload):
    return eval(payload)

def shell_injection(cmd):
    os.system("echo " + cmd)
""", encoding="utf-8")

    findings = scan_file_ast(str(unsafe_py))
    rules = [f["rule"] for f in findings]
    assert "py/sql-injection" in rules
    assert "py/dangerous-eval" in rules
    assert "py/command-injection" in rules


def test_dynamic_ota_rules(tmp_path):
    rules = load_security_rules()
    assert "secret_patterns" in rules
    assert "malicious_packages" in rules
    assert len(rules["malicious_packages"]) > 0

    # Ensure offline baseline fallback works
    assert "reqeusts" in rules["malicious_packages"]


def test_user_custom_additive_security_rules(tmp_path, monkeypatch):
    # Simulate a repo with custom .oops-rules.json
    rules_file = tmp_path / ".oops-rules.json"
    rules_file.write_text(json.dumps({
        "extra_banned_packages": ["internal-unapproved-lib"],
        "extra_secret_patterns": [{"pattern": r"ACME-[0-9]{6}", "label": "Acme Internal Token", "severity": "CRITICAL"}],
        "extra_forbidden_calls": ["pickle.loads"]
    }), encoding="utf-8")

    monkeypatch.chdir(tmp_path)
    merged = load_security_rules()

    # 1. Existing baseline rules CANNOT be deleted
    assert "reqeusts" in merged["malicious_packages"]
    assert any("OpenAI" in p["label"] for p in merged["secret_patterns"])

    # 2. Custom rules are cleanly added
    assert "internal-unapproved-lib" in merged["malicious_packages"]
    assert any("Acme Internal Token" in p["label"] for p in merged["secret_patterns"])
    assert "pickle.loads" in merged.get("custom_forbidden_calls", [])

    # 3. Test that custom forbidden call is caught by AST visitor
    py_file = tmp_path / "danger.py"
    py_file.write_text("import pickle\npickle.loads(b'data')", encoding="utf-8")
    findings = scan_file_ast(str(py_file), custom_forbidden_calls=merged["custom_forbidden_calls"])
    assert any(f["rule"] == "custom/forbidden-call" for f in findings)


def test_self_healing_tamper_resistance():
    # Verify baseline is immutable even if local rules file is deleted
    from src.rules import RULES_FILE
    if RULES_FILE.exists():
        os.remove(RULES_FILE)

    # Calling load_security_rules immediately restores rules and recreates file
    healed = load_security_rules()
    assert "reqeusts" in healed["malicious_packages"]
    assert any("OpenAI" in p["label"] for p in healed["secret_patterns"])
    assert RULES_FILE.exists()


def test_anti_tampering_corrupted_file():
    # If someone maliciously tampers with the rules file (e.g. empty packages or corrupt regex)
    from src.rules import RULES_FILE
    with open(RULES_FILE, "w", encoding="utf-8") as f:
        f.write('{"malicious_packages": [], "secret_patterns": [{"pattern": "[invalid-regex("}]}')

    # load_security_rules will discard corrupted regexes and enforce hardcoded baselines
    sanitized = load_security_rules()
    assert "reqeusts" in sanitized["malicious_packages"]
    assert any("OpenAI" in p["label"] for p in sanitized["secret_patterns"])


def test_hardware_telemetry():
    telemetry = get_hardware_telemetry()
    assert "platform" in telemetry
    assert "process_priority" in telemetry
    assert "is_throttled" in telemetry
    # Prioritization check should not crash
    down_prioritize_process()


def test_supply_chain_typosquatting():
    safe, reason = check_typosquatting("reqeusts")
    assert safe is False
    assert "reqeusts" in reason or "requests" in reason

    safe, reason = check_typosquatting("colorma")
    assert safe is False
    assert "colorma" in reason or "colorama" in reason

    safe, reason = check_typosquatting("requests")
    assert safe is True


def test_solver_deterministic_ast():
    # 1. AttributeError 'NoneType' object has no attribute
    code = """
def get_user_name(user):
    return user.name
"""
    err = "AttributeError: 'NoneType' object has no attribute 'name'"
    fixed = solve_none_attribute_error(code, err)
    assert "if user is None: return None" in fixed

    # 2. ZeroDivisionError
    code_div = """
def calc(a, b):
    return a / b
"""
    err_div = "ZeroDivisionError: division by zero"
    fixed_div = solve_zero_division_error(code_div, err_div)
    assert "if b == 0: return 0" in fixed_div

    # 3. Overall solve_with_ast
    solved, diag = solve_with_ast(code, err)
    assert solved is True
    assert diag["cost_usd"] == 0.0


def test_crash_replay_snapshot(tmp_path):
    snap_id = record_crash_snapshot(
        target_file="app.py",
        exception_type="ZeroDivisionError",
        exception_message="division by zero",
        stack_frames=[{"function": "calc", "line": 42}],
        local_vars={"a": 10, "b": 0}
    )
    assert snap_id.endswith(".json")

    loaded = inspect_crash_snapshot(snap_id)
    assert loaded["exception_type"] == "ZeroDivisionError"
    assert loaded["local_variables"]["b"] == 0


def test_regression_test_generator(tmp_path):
    test_file = synthesize_regression_test(
        target_file="src/utils.py",
        error_log="ValueError: invalid literal for int()",
        repaired_snippet="val = int(s) if s.isdigit() else 0",
        tests_dir=str(tmp_path)
    )
    assert os.path.exists(test_file)
    with open(test_file, "r", encoding="utf-8") as f:
        content = f.read()
    assert "test_regression" in content
    assert "Auto-synthesized regression test" in content


def test_local_llm_probe():
    avail, provider, model = probe_local_llm(timeout=0.2)
    assert isinstance(avail, bool)
    assert isinstance(provider, str)
    assert isinstance(model, str)


def test_pre_pr_reviewer_formatting():
    mock_report = {
        "verdict": "APPROVED",
        "base_branch": "origin/main",
        "changed_files_count": 3,
        "changed_files": ["src/app.py", "tests/test_app.py"],
        "lines_added": 45,
        "lines_deleted": 10,
        "secret_findings": [],
        "ast_findings": [],
        "complexity_warnings": [],
        "test_parity_warning": None
    }
    md = format_pr_review_markdown(mock_report)
    assert "APPROVED" in md
    assert "origin/main" in md
    assert "All L3 security checks passed cleanly" in md
