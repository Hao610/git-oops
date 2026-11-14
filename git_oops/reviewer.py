"""
Git-Oops Pre-PR Gatekeeper & Staff Engineer Audit Engine
Audits outgoing branch changes against base branch before Pull Request creation.
Verifies L3 security, complexity drift, test coverage parity, and secret leaks.
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Tuple

from git_oops.hooks import scan_diff_for_secrets, scan_file_ast
from git_oops.sentinel import check_code_complexity


def get_default_base_branch() -> str:
    """Detects default remote base branch (origin/main or main or master)."""
    for candidate in ("origin/main", "main", "origin/master", "master"):
        res = subprocess.run(
            ["git", "rev-parse", "--verify", candidate],
            capture_output=True, text=True, errors="replace"
        )
        if res.returncode == 0:
            return candidate
    return "HEAD~1"


def review_pull_request(base_branch: str = None) -> Dict[str, Any]:
    """
    Performs comprehensive Pre-PR audit:
    - Diff analysis vs base_branch
    - Secret & token leak inspection
    - AST security (CodeQL CWE mirrors)
    - Code bloat & complexity check
    - Test parity verification
    """
    base = base_branch or get_default_base_branch()

    # Get diff against base
    diff_proc = subprocess.run(
        ["git", "diff", f"{base}...HEAD"],
        capture_output=True, text=True, errors="replace"
    )
    diff_text = diff_proc.stdout

    # Get changed files
    files_proc = subprocess.run(
        ["git", "diff", "--name-only", f"{base}...HEAD"],
        capture_output=True, text=True, errors="replace"
    )
    changed_files = [f.strip() for f in files_proc.stdout.splitlines() if f.strip()]

    # 1. Secret scanning
    secret_findings = scan_diff_for_secrets(diff_text)

    # 2. AST security & complexity on modified Python files
    ast_findings: List[Dict[str, Any]] = []
    complexity_warnings: List[Dict[str, Any]] = []

    src_changed = False
    tests_changed = False

    for fpath in changed_files:
        if fpath.startswith("tests/") or "test" in fpath.lower():
            tests_changed = True
        elif fpath.startswith("src/") or fpath.endswith(".py"):
            src_changed = True

        if fpath.endswith(".py") and os.path.exists(fpath):
            findings = scan_file_ast(fpath)
            ast_findings.extend(findings)

            # Check complexity
            try:
                with open(fpath, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read()
                ok, err = check_code_complexity(content, max_allowed_complexity=12)
                if not ok:
                    complexity_warnings.append({"file": fpath, "details": err})
            except Exception:
                pass

    # 3. Test parity warning
    test_parity_warning = None
    if src_changed and not tests_changed:
        test_parity_warning = "Application code modified without accompanying test updates in tests/."

    # Determine verdict
    critical_issues = len(secret_findings) + len([f for f in ast_findings if f.get("severity") in ("CRITICAL", "HIGH")])
    if critical_issues > 0:
        verdict = "BLOCKED"
    elif complexity_warnings or test_parity_warning:
        verdict = "WARNINGS"
    else:
        verdict = "APPROVED"

    # Churn stats
    added_lines = sum(1 for line in diff_text.splitlines() if line.startswith("+") and not line.startswith("+++"))
    deleted_lines = sum(1 for line in diff_text.splitlines() if line.startswith("-") and not line.startswith("---"))

    report = {
        "verdict": verdict,
        "base_branch": base,
        "changed_files_count": len(changed_files),
        "changed_files": changed_files,
        "lines_added": added_lines,
        "lines_deleted": deleted_lines,
        "secret_findings": secret_findings,
        "ast_findings": ast_findings,
        "complexity_warnings": complexity_warnings,
        "test_parity_warning": test_parity_warning
    }
    return report


def format_pr_review_markdown(report: Dict[str, Any]) -> str:
    """Formats PR audit report as clean GitHub Flavored Markdown."""
    verdict = report["verdict"]
    badge = "🟢 **APPROVED**" if verdict == "APPROVED" else ("🟡 **WARNINGS**" if verdict == "WARNINGS" else "🔴 **BLOCKED**")

    lines = [
        "## 🛡️ Git-Oops Pre-PR Gatekeeper Audit Report",
        "",
        f"**Verdict**: {badge} (Base branch: `{report['base_branch']}`)",
        f"**Diff Churn**: `{report['changed_files_count']}` files modified (+{report['lines_added']} / -{report['lines_deleted']} lines)",
        ""
    ]

    if report["secret_findings"]:
        lines.append("### 🚨 Critical Secret Leaks Detected")
        for s in report["secret_findings"]:
            lines.append(f"- **{s['label']}** at line {s['line']}: `{s['snippet']}`")
        lines.append("")

    if report["ast_findings"]:
        lines.append("### ⚠️ AST Security & CodeQL Violations")
        for a in report["ast_findings"]:
            lines.append(f"- **[{a.get('severity', 'HIGH')}] {a.get('rule', 'AST')}** in `{a.get('file')}:{a.get('line')}`: {a.get('msg')}")
        lines.append("")

    if report["test_parity_warning"]:
        lines.append("### 🧪 Test Parity Notice")
        lines.append(f"- ⚠️ {report['test_parity_warning']}")
        lines.append("")

    if report["complexity_warnings"]:
        lines.append("### 📈 Complexity Drift")
        for c in report["complexity_warnings"]:
            lines.append(f"- `{c['file']}`: {c['details']}")
        lines.append("")

    if verdict == "APPROVED":
        lines.append("✨ All L3 security checks passed cleanly. Ready for production merge!")

    return "\n".join(lines)
