"""
Git-Oops CLI Entrypoint
Interactive terminal UX with rich color support and safety controls.
Usage:
  git-oops --file src/app.py --error "TypeError: ..."
  git-oops --status
  git-oops --set-budget 2.0
"""

import sys
import os
import json
import argparse
import subprocess

# Ensure standard UTF-8 output on Windows consoles to prevent cp1252 charmap crashes
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from src.circuit_breaker import (
    get_daily_spend,
    get_default_config,
    set_config_value,
    check_release_velocity,
)
from src.engine import diagnose_and_patch, apply_patch_to_file, rollback_file
from src.firewall import check_command_safety
from src.squeezer import compress_traceback
from src.watchdog import (
    check_anti_thrashing,
    freeze_workstation,
    unfreeze_workstation,
    kill_orphaned_agents,
)
from src.guardian import verify_patch_in_sandbox, check_ghost_imports
from src.blackbox import record_step, rewind_step, list_flight_events, register_antibody, match_antibody
from src.mcp_server import run_mcp_server
from src.shadow import ShadowWorkspace
from src.consensus import arbitrate_consensus
from src.sentinel import (
    check_egress_security,
    check_license_taint,
    check_code_complexity,
    check_nesting_and_complexity,
)
from src.hud import start_hud_server
from src.hooks import (
    run_l3_preflight,
    run_pre_push_check,
    setup_global_hooks,
    ensure_auto_hooks,
    set_task_scope,
    clear_task_scope,
)
from src.rules import trigger_ota_update_background, sync_security_rules_foreground
from src.replay import inspect_crash_snapshot
from src.salvage import run_reflog_autopsy
from src.solver import solve_with_ast
from src.supply_chain import scan_dependencies_file
from src.reviewer import review_pull_request, format_pr_review_markdown
from src.hardware import get_hardware_telemetry
from src.tester import synthesize_regression_test
from src.ui import (
    print_banner,
    draw_card,
    render_diff,
    spin_task,
    FG_CYAN,
    FG_MAGENTA,
    FG_YELLOW,
    FG_GREEN,
    FG_RED,
    FG_WHITE,
    FG_GRAY,
    BOLD,
    ITALIC,
    RESET,
)


def _emit_gate_result(agent_mode: bool, payload: dict, title: str, msg: str, color: str) -> None:
    if agent_mode:
        print(json.dumps(payload))
    else:
        print_banner()
        draw_card(title, msg, color_border=color, color_title=color)


def _handle_freeze_and_sweep(args) -> bool:
    if args.freeze:
        ok, msg = freeze_workstation()
        _emit_gate_result(args.agent_mode, {"frozen": ok, "message": msg}, "EMERGENCY HARDWARE FREEZE", msg, FG_RED)
        return True
    if args.unfreeze:
        ok, msg = unfreeze_workstation()
        _emit_gate_result(args.agent_mode, {"unfrozen": ok, "message": msg}, "WORKSTATION UNFROZEN", msg, FG_GREEN)
        return True
    if args.kill_agents:
        count, killed = kill_orphaned_agents()
        msg = f"Terminated {count} detached agent process(es): {', '.join(killed) if killed else 'None found'}."
        _emit_gate_result(args.agent_mode, {"killed_count": count, "pids": killed}, "AGENT PROCESS SWEEP", msg, FG_YELLOW)
        return True
    return False


def _handle_scope_and_gates(args) -> bool:
    if args.scope is not None:
        if args.scope.strip().lower() == "clear":
            clear_task_scope()
            msg = "Cleared active L6 task scope restrictions."
        else:
            patterns = [p.strip() for p in args.scope.split(",") if p.strip()]
            cfg = set_task_scope(patterns, max_files=args.max_files)
            msg = f"L6 Scope locked to: {cfg['patterns']} (max_files: {cfg['max_files']})."
        _emit_gate_result(args.agent_mode, {"scope_updated": True, "message": msg}, "L6 INTENT SCOPE LIMITER", msg, FG_CYAN)
        return True

    if args.check_velocity:
        ok, msg = check_release_velocity()
        _emit_gate_result(args.agent_mode, {"allowed": ok, "message": msg}, "RELEASE VELOCITY BREAKER", msg, FG_GREEN if ok else FG_RED)
        if not ok:
            sys.exit(1)
        return True

    if args.verify_gate:
        if not os.path.exists(args.verify_gate):
            print(json.dumps({"passed": False, "error": f"File not found: {args.verify_gate}"}))
            sys.exit(1)
        with open(args.verify_gate, "r", encoding="utf-8", errors="replace") as f:
            ok, reason = check_nesting_and_complexity(f.read())
        msg = reason or f"L4 Quality Gate PASSED for '{args.verify_gate}'."
        _emit_gate_result(args.agent_mode, {"passed": ok, "file": args.verify_gate, "reason": reason}, "L4 QUALITY & ANTI-SLOP GATE", msg, FG_GREEN if ok else FG_RED)
        if not ok:
            sys.exit(1)
        return True
    return False


def _handle_governance_flags(args) -> bool:
    """Handles v1.2.1 Sovereign Governance & Anti-Slop CLI flags."""
    return _handle_freeze_and_sweep(args) or _handle_scope_and_gates(args)


def _handle_hooks_and_hud(args) -> bool:
    if args.update_rules:
        ok, msg = sync_security_rules_foreground(force=True)
        _emit_gate_result(args.agent_mode, {"success": ok, "message": msg}, "DYNAMIC OTA SECURITY RULES", msg, FG_GREEN if ok else FG_YELLOW)
        return True
    if args.hud:
        start_hud_server()
        return True
    if args.pre_commit:
        passed, violations, report = run_l3_preflight()
        print(json.dumps({"passed": passed, "violations_count": len(violations), "violations": violations}) if args.agent_mode else report)
        sys.exit(0 if passed else 1)
    if args.pre_push:
        passed, report = run_pre_push_check()
        print(json.dumps({"passed": passed, "report": report}) if args.agent_mode else report)
        sys.exit(0 if passed else 1)
    if args.install_hooks:
        ok, msg = setup_global_hooks(force=True)
        _emit_gate_result(args.agent_mode, {"success": ok, "message": msg}, "GLOBAL GIT HOOKS", msg, FG_GREEN if ok else FG_RED)
        return True
    if args.mcp:
        run_mcp_server()
        return True
    return False


def _handle_replay_and_salvage(args) -> bool:
    if args.replay:
        snap = inspect_crash_snapshot(args.replay)
        if args.agent_mode:
            print(json.dumps(snap))
        else:
            print_banner()
            if snap.get("status") == "NOT_FOUND":
                draw_card("CRASH REPLAY", f"Snapshot '{args.replay}' not found.", color_border=FG_RED, color_title=FG_RED)
            else:
                body = f"Timestamp: {snap.get('timestamp')}\nTarget: {snap.get('target_file')}\nException: {snap.get('exception_type')}: {snap.get('exception_message')}\n\nLocal Variables:\n{json.dumps(snap.get('local_variables', {}), indent=2)}"
                draw_card("CRASH REPLAY TIME MACHINE", body, color_border=FG_CYAN, color_title=FG_CYAN)
        return True

    if args.salvage:
        recovered = run_reflog_autopsy()
        if args.agent_mode:
            print(json.dumps({"recovered_count": len(recovered), "commits": recovered}))
        else:
            print_banner()
            if recovered:
                commits_str = "\n".join([f"• [{c['sha'][:7]}] {c['subject']} (Lost at: {c['reflog_action']})" for c in recovered[:10]])
                draw_card("REFLOG AUTOPSY RESCUE", f"Rescued {len(recovered)} lost commit snapshots:\n\n{commits_str}", color_border=FG_GREEN, color_title=FG_GREEN)
            else:
                draw_card("REFLOG AUTOPSY", "No lost or orphaned commits detected in reflog.", color_border=FG_CYAN, color_title=FG_CYAN)
        return True
    return False


def _handle_audit_commands(args) -> bool:
    if args.supply_chain:
        results = scan_dependencies_file(args.supply_chain)
        if args.agent_mode:
            print(json.dumps(results))
        else:
            print_banner()
            res_str = f"Scanned {results['scanned_packages_count']} dependencies in '{args.supply_chain}'.\n\n"
            if results["violations"]:
                res_str += "🚨 VIOLATIONS DETECTED:\n" + "\n".join([f"• {v['package']}: {v['details']}" for v in results["violations"]])
                draw_card("SUPPLY CHAIN SECURITY ALERT", res_str, color_border=FG_RED, color_title=FG_RED)
            else:
                res_str += "✅ Zero typosquatting or malicious packages detected."
                draw_card("SUPPLY CHAIN SECURITY PASSED", res_str, color_border=FG_GREEN, color_title=FG_GREEN)
        return True

    if args.review_pr is not None:
        target_b = None if args.review_pr == "DEFAULT" else args.review_pr
        report = review_pull_request(target_b)
        if args.agent_mode:
            print(json.dumps(report))
        else:
            print_banner()
            border_c = FG_GREEN if report["verdict"] == "APPROVED" else (FG_YELLOW if report["verdict"] == "WARNINGS" else FG_RED)
            draw_card("PRE-PR GATEKEEPER AUDIT", format_pr_review_markdown(report), color_border=border_c, color_title=border_c)
        return True

    if args.hardware:
        hw = get_hardware_telemetry()
        b_text = f"{hw['battery_percent']}%" if hw["battery_percent"] else "N/A"
        hw_str = f"Operating System  : {hw['platform']}\nBattery Level     : {b_text} (Plugged in: {hw['power_plugged']})\nProcess Priority  : {hw['process_priority']}\nThrottle Active   : {'YES' if hw['is_throttled'] else 'NO'}"
        _emit_gate_result(args.agent_mode, hw, "HARDWARE & THROTTLE TELEMETRY", hw_str, FG_CYAN)
        return True
    return False


def _handle_flight_and_config(args) -> bool:
    if args.rewind is not None:
        ok = rewind_step(args.rewind)
        msg = f"Successfully rewound file to snapshot from step {args.rewind}." if ok else f"Could not find snapshot for step {args.rewind}."
        _emit_gate_result(args.agent_mode, {"success": ok, "rewound_to_step": args.rewind}, "FLIGHT RECORDER REWIND" if ok else "REWIND FAILED", msg, FG_GREEN if ok else FG_RED)
        return True

    if args.flight_log:
        events = list_flight_events(limit=10)
        log_str = "\n".join([f"• [{e['step_id']}] {e['timestamp']} - {e['action']} on {e['target_file']}: {e['motivation']}" for e in events]) if events else "No events recorded yet."
        _emit_gate_result(args.agent_mode, {"events": events}, "BLACKBOX FLIGHT RECORDER LOG", log_str, FG_CYAN)
        return True

    if args.set_personality:
        set_config_value("personality", args.set_personality)
        print_banner()
        draw_card("CONFIGURATION SAVED", f"Default persona updated to: {FG_YELLOW}{BOLD}{args.set_personality}{RESET}\nAll future crashes will be roasted in this style.", color_border=FG_GREEN, color_title=FG_GREEN)
        return True

    if args.set_budget is not None:
        set_config_value("daily_budget", args.set_budget)
        print_banner()
        draw_card("CIRCUIT BREAKER UPDATED", f"Daily spending limit hard-capped at: {FG_GREEN}{BOLD}${args.set_budget:.2f} USD{RESET}\nRequests will automatically abort if spend exceeds this threshold.", color_border=FG_GREEN, color_title=FG_GREEN)
        return True

    if args.status:
        spent = get_daily_spend()
        print_banner()
        status_text = (
            f"Accumulated Spend Today : {FG_GREEN}{BOLD}${spent:.5f} USD{RESET}\n"
            f"Daily Safety Ceiling    : {FG_YELLOW}{BOLD}${args.budget:.2f} USD{RESET}\n"
            f"Remaining Budget Safe   : {FG_CYAN}{BOLD}${max(0.0, args.budget - spent):.5f} USD{RESET}\n"
            f"Active Roast Persona    : {FG_MAGENTA}{BOLD}{args.personality}{RESET}"
        )
        draw_card("CIRCUIT BREAKER METRICS", status_text, color_border=FG_CYAN, color_title=FG_WHITE)
        return True

    if args.undo:
        success = rollback_file(args.undo)
        print_banner()
        if success:
            draw_card("SAFETY ROLLBACK", f"Successfully restored {BOLD}'{args.undo}'{RESET} from its previous backup snapshot.\nOriginal code state reinstated.", color_border=FG_GREEN, color_title=FG_GREEN)
        else:
            draw_card("ROLLBACK FAILED", f"No safety backup found for {BOLD}'{args.undo}'{RESET}.\nExpected snapshot: '{args.undo}.oops.bak'", color_border=FG_RED, color_title=FG_RED)
        return True
    return False


def _handle_run_command(args) -> bool:
    """Executes --run command safely. Returns True if caller should exit."""
    if not args.run:
        return False
    safe, reason = check_command_safety(args.run)
    if not safe:
        _emit_gate_result(args.agent_mode, {"status": "BLOCKED", "reason": reason}, "BLAST-RADIUS FIREWALL VIOLATION", reason, FG_RED)
        return True

    if not args.agent_mode:
        print_banner()
        draw_card("COMMAND RUNNER", f"Executing: {args.run}\nInterception active.", color_border=FG_CYAN, color_title=FG_CYAN)

    proc = subprocess.run(args.run, shell=True, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if proc.returncode == 0:
        if args.agent_mode:
            print(json.dumps({"status": "SUCCESS", "exit_code": 0, "stdout": proc.stdout}))
        else:
            print(proc.stdout)
            draw_card("EXECUTION SUCCESS", "Command completed cleanly without errors.", color_border=FG_GREEN, color_title=FG_GREEN)
        return True

    raw_err = (proc.stderr or "") + "\n" + (proc.stdout or "")
    args.error = compress_traceback(raw_err)
    if not args.file:
        import re
        for cand in reversed(re.findall(r'File "([^"]+)", line \d+', raw_err)):
            if os.path.exists(cand):
                args.file = cand
                break
    return False


def _run_diagnosis_pipeline(args, filepath: str, file_content: str):
    if args.solver:
        solved_ast, sym_diag = solve_with_ast(file_content, args.error)
        if solved_ast and sym_diag:
            if not args.agent_mode:
                draw_card("1MS DETERMINISTIC AST SYMBOLIC SOLVER", "Resolved crash deterministically in 1ms with ZERO LLM queries & zero token cost.", color_border=FG_GREEN, color_title=FG_GREEN)
            return sym_diag

    if args.consensus:
        reached, diagnosis, arb_summary = arbitrate_consensus(
            error_log=args.error, file_context=file_content, target_filepath=filepath, budget_limit_usd=args.budget
        )
        if not args.agent_mode:
            border_c = FG_GREEN if reached else FG_YELLOW
            draw_card("CROSS-MODEL ARBITRATION CONSENSUS", arb_summary, color_border=border_c, color_title=border_c)
        return diagnosis

    return diagnose_and_patch(
        error_log=args.error, file_context=file_content, target_filepath=filepath,
        personality=args.personality, budget_limit_usd=args.budget,
    )


def _validate_patch_safety(args, filepath: str, diagnosis: dict) -> bool:
    patch_str = str(diagnosis.get("git_patch", ""))
    snippet = diagnosis["fixed_snippet"]
    checks = [
        (*check_anti_thrashing(filepath, patch_str), "ANTI_THRASHING_HALT", "ANTI-THRASHING WATCHDOG TRIGGERED"),
        (*check_ghost_imports(snippet, filepath=filepath), "GHOST_IMPORT_REJECTED", "GHOST IMPORT LINTER HALT"),
        (*verify_patch_in_sandbox(filepath, diagnosis["original_snippet"], snippet), "REGRESSION_GUARD_REJECTED", "REGRESSION GUARD REJECTION"),
        (*check_egress_security(snippet), "EGRESS_SECURITY_BLOCKED", "EGRESS NETWORK SECURITY ALERT"),
        (*check_license_taint(snippet), "LICENSE_TAINT_BLOCKED", "LICENSE TAINT DETECTED"),
    ]
    for ok, err_msg, code, title in checks:
        if not ok:
            _emit_gate_result(args.agent_mode, {"error": code, "details": err_msg}, title, err_msg, FG_RED)
            return False

    bloat_ok, bloat_err = check_code_complexity(snippet, max_allowed_complexity=8)
    if not bloat_ok:
        _emit_gate_result(args.agent_mode, {"error": "ANTI_BLOAT_VIOLATION", "details": bloat_err}, "ANTI-BLOAT COMPLEXITY WARNING", bloat_err, FG_YELLOW)
    return True


def _apply_and_report_patch(args, filepath: str, diagnosis: dict) -> None:
    patch_str = str(diagnosis.get("git_patch", ""))
    if args.shadow:
        with ShadowWorkspace() as shadow:
            if not args.agent_mode:
                draw_card("SHADOW WORKSPACE ISOLATION", f"Dry-running patch inside temporary shadow container: {shadow.shadow_dir}", color_border=FG_CYAN, color_title=FG_CYAN)
            if apply_patch_to_file(os.path.join(shadow.shadow_dir, filepath), diagnosis["original_snippet"], diagnosis["fixed_snippet"]):
                shadow.commit_file_to_real(filepath)

    if args.agent_mode:
        if args.yes:
            applied = apply_patch_to_file(filepath, diagnosis["original_snippet"], diagnosis["fixed_snippet"])
            step_id = record_step("agent", "apply_patch", filepath, diagnosis["root_cause"], patch_str)
            register_antibody(args.error[:100], diagnosis["fixed_snippet"], diagnosis["root_cause"])
            print(json.dumps({"status": "APPLIED" if applied else "PATCH_FAILED", "target_file": filepath, "step_id": step_id, "roast": diagnosis["roast"], "root_cause": diagnosis["root_cause"], "cost_usd": diagnosis.get("cost_usd", 0.0), "is_cached": diagnosis.get("is_cached", False)}))
        else:
            print(json.dumps({"status": "PROPOSED", "target_file": filepath, "diff": patch_str, "roast": diagnosis["roast"], "root_cause": diagnosis["root_cause"], "original_snippet": diagnosis["original_snippet"], "fixed_snippet": diagnosis["fixed_snippet"], "cost_usd": diagnosis.get("cost_usd", 0.0), "is_cached": diagnosis.get("is_cached", False)}))
        return

    draw_card(f"CRITIC ROAST ({args.personality.upper()})", f"{FG_YELLOW}{ITALIC}\"{diagnosis['roast']}\"{RESET}", color_border=FG_MAGENTA, color_title=FG_MAGENTA)
    cost_str = f"${diagnosis.get('cost_usd', 0.0):.5f} USD" if not diagnosis.get("is_cached") else "FREE (Deterministic Cache Hit)"
    meta_text = f"Root Cause   : {BOLD}{diagnosis['root_cause']}{RESET}\nTarget File  : {FG_CYAN}{filepath}{RESET}\nQuery Cost   : {FG_GREEN}{cost_str}{RESET}  │  Today's Total: ${get_daily_spend():.4f} USD\nSafety Check : {FG_GREEN}Circuit Breaker Passed (Limit: ${args.budget:.2f}){RESET}"
    draw_card("DIAGNOSTIC ANALYSIS & FINANCIAL METRICS", meta_text, color_border=FG_CYAN, color_title=FG_CYAN)
    print(f"\n{BOLD}{FG_WHITE}PROPOSED SURGICAL GIT PATCH:{RESET}\n")
    render_diff(patch_str)
    print("")

    confirm = args.yes or input(f" {FG_YELLOW}{BOLD}?{RESET} {BOLD}Apply this patch to '{filepath}' right now? [y/N]: {RESET}").strip().lower() in ("y", "yes")
    if not confirm:
        print(f"\n {FG_GRAY}Aborted. No files were modified.{RESET}\n")
        return
    if apply_patch_to_file(filepath, diagnosis["original_snippet"], diagnosis["fixed_snippet"]):
        draw_card("PATCH APPLIED SUCCESSFULLY", f"File '{filepath}' updated safely.\nRun `git-oops --undo {filepath}` if you wish to roll back.", color_border=FG_GREEN, color_title=FG_GREEN)
        if args.test_gen:
            tpath = synthesize_regression_test(filepath, args.error, diagnosis["fixed_snippet"])
            draw_card("REGRESSION TEST SYNTHESIZED", f"Synthesized permanent regression test: {tpath}", color_border=FG_GREEN, color_title=FG_GREEN)
    else:
        draw_card("PATCH APPLICATION FAILED", "Original snippet did not match cleanly.", color_border=FG_RED, color_title=FG_RED)


def _build_arg_parser(saved_cfg: dict) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="git-oops", description="Brutally honest terminal crash fixer with daily spend-protection circuit breaker.")
    parser.add_argument("-v", "--version", action="version", version="git-oops v1.2.1 (The Sovereign AI Governance Edition)")
    parser.add_argument("-f", "--file", help="Path to the file that crashed", default=None)
    parser.add_argument("-e", "--error", help="Error message or traceback string", default=None)
    parser.add_argument("-b", "--budget", help="Daily API spend ceiling in USD (default: $1.00)", type=float, default=saved_cfg.get("daily_budget", 1.0))
    parser.add_argument("-p", "--personality", help="Roast persona: 'staff', 'kernel', 'chef', or 'passive_aggressive'", default=saved_cfg.get("personality", "staff"), choices=["staff", "kernel", "chef", "passive_aggressive"])
    parser.add_argument("--set-personality", help="Permanently save default roast persona", choices=["staff", "kernel", "chef", "passive_aggressive"])
    parser.add_argument("--set-budget", help="Permanently save default daily spend budget in USD", type=float)
    parser.add_argument("-y", "--yes", help="Auto-apply patch without interactive prompt", action="store_true")
    parser.add_argument("-u", "--undo", help="Roll back the last applied patch on target file", default=None)
    parser.add_argument("-r", "--run", help="Execute a command and auto-catch its crash (e.g. -r 'python app.py')", default=None)
    parser.add_argument("-s", "--status", help="Show today's accumulated API spend", action="store_true")
    parser.add_argument("-a", "--agent", "--json", dest="agent_mode", help="Headless Agent mode: emits machine-readable JSON without ANSI codes", action="store_true")
    parser.add_argument("-m", "--mcp", help="Start git-oops as a native Model Context Protocol (MCP) server over stdio", action="store_true")
    parser.add_argument("--rewind", help="Flight Recorder: rewind codebase to a previous step ID", type=int, default=None)
    parser.add_argument("--flight-log", help="Display recent blackbox flight recorder steps", action="store_true")
    parser.add_argument("--shadow", help="Run repair verification inside an isolated temporary shadow workspace", action="store_true")
    parser.add_argument("--consensus", help="Multi-LLM cross-arbitration: require two models to reach consensus before patching", action="store_true")
    parser.add_argument("--hud", help="Start Obsidian Glassmorphism Web HUD server", action="store_true")
    parser.add_argument("--pre-commit", help="Execute sub-second L3 pre-commit security pre-flight", action="store_true")
    parser.add_argument("--pre-push", help="Execute pre-push branch and outgoing commit verification", action="store_true")
    parser.add_argument("--install-hooks", help="Force install machine-wide git hooks via core.hooksPath", action="store_true")
    parser.add_argument("--replay", help="Inspect crash variable snapshot (e.g. --replay crash_123.json)", default=None)
    parser.add_argument("--salvage", help="Execute git reflog autopsy to rescue lost commits", action="store_true")
    parser.add_argument("--solver", help="Zero-AI 1ms deterministic AST symbolic crash solver", action="store_true")
    parser.add_argument("--supply-chain", help="Audit dependencies file for typosquatting & vulnerabilities", default=None)
    parser.add_argument("--review-pr", help="Pre-PR gatekeeper audit against target branch (default: origin/main)", nargs="?", const="DEFAULT", default=None)
    parser.add_argument("--hardware", help="Display hardware telemetry and CPU throttling metrics", action="store_true")
    parser.add_argument("--test-gen", help="Generate permanent regression test for error", action="store_true")
    parser.add_argument("--local", "--ollama", dest="local_mode", help="Use local offline LLM (Ollama/vLLM) instead of cloud APIs", action="store_true")
    parser.add_argument("--update-rules", help="Force OTA update of L3 dynamic security rules", action="store_true")
    parser.add_argument("--freeze", help="Emergency Hardware Freeze: block all git mutations immediately", action="store_true")
    parser.add_argument("--unfreeze", help="Clear Emergency Hardware Freeze lockfile", action="store_true")
    parser.add_argument("--kill-agents", help="Terminate orphaned detached AI agent subshells", action="store_true")
    parser.add_argument("--scope", help="Set L6 allowed path prefixes (comma-separated) or 'clear'", default=None)
    parser.add_argument("--max-files", help="Max staged files allowed under active L6 scope", type=int, default=None)
    parser.add_argument("--check-velocity", help="Check release velocity circuit breaker", action="store_true")
    parser.add_argument("--verify-gate", help="Run L4 Anti-Slop complexity & nesting gate on a Python file", default=None)
    return parser


def _resolve_crash_input(args) -> bool:
    """Ensures --file and --error are populated (from args or stdin). Returns True if ready."""
    if not args.file or not args.error:
        if not sys.stdin.isatty():
            args.error = sys.stdin.read().strip()
        if not args.file or not args.error:
            print(f"{FG_RED}Error: Must provide --file and --error (or pipe error via stdin).{RESET}")
            print(f"Example: {FG_CYAN}git-oops --file app.py --error \"NameError: name 'x' is not defined\"{RESET}")
            return False
    if not os.path.exists(args.file):
        print(json.dumps({"error": f"File '{args.file}' not found"}) if args.agent_mode else f"{FG_RED}Error: File '{args.file}' not found.{RESET}")
        return False
    return True


def _dispatch_early_handlers(args) -> bool:
    handlers = (
        _handle_governance_flags,
        _handle_hooks_and_hud,
        _handle_replay_and_salvage,
        _handle_audit_commands,
        _handle_flight_and_config,
        _handle_run_command,
    )
    return any(handler(args) for handler in handlers)


def main():
    args = _build_arg_parser(get_default_config()).parse_args()
    ensure_auto_hooks()
    trigger_ota_update_background()

    if _dispatch_early_handlers(args) or not _resolve_crash_input(args):
        return

    filepath = args.file
    with open(filepath, "r", encoding="utf-8") as f:
        file_content = f.read()

    antibody = match_antibody(args.error)
    if antibody and not args.agent_mode:
        draw_card("ANTIBODY IMMUNITY RECALL", f"Recognized known architectural pattern:\n{antibody['explanation']}", color_border=FG_GREEN, color_title=FG_GREEN)
    if not args.agent_mode:
        print_banner()
        spin_task("Analyzing stack trace & scanning codebase boundaries...", duration=0.6)
        spin_task(f"Invoking critic persona '{args.personality.upper()}'...", duration=0.5)

    try:
        diagnosis = _run_diagnosis_pipeline(args, filepath, file_content)
    except PermissionError as pe:
        _emit_gate_result(args.agent_mode, {"error": "CIRCUIT_BREAKER_TRIGGERED", "details": str(pe)}, "CIRCUIT BREAKER TRIGGERED", str(pe), FG_RED)
        return
    except Exception as ex:
        _emit_gate_result(args.agent_mode, {"error": "DIAGNOSTIC_FAILED", "details": str(ex)}, "DIAGNOSTIC ERROR", str(ex), FG_RED)
        return

    if _validate_patch_safety(args, filepath, diagnosis):
        _apply_and_report_patch(args, filepath, diagnosis)


if __name__ == "__main__":
    main()
