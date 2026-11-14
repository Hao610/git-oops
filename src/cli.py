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

from src.circuit_breaker import get_daily_spend, get_default_config, set_config_value
from src.engine import diagnose_and_patch, apply_patch_to_file, rollback_file
from src.firewall import check_command_safety
from src.squeezer import compress_traceback, redact_secrets
from src.watchdog import check_anti_thrashing, acquire_agent_lock, release_agent_lock
from src.guardian import verify_patch_in_sandbox, check_ghost_imports
from src.blackbox import record_step, rewind_step, list_flight_events, register_antibody, match_antibody
from src.mcp_server import run_mcp_server
from src.shadow import ShadowWorkspace
from src.consensus import arbitrate_consensus
from src.sentinel import check_egress_security, check_license_taint, check_code_complexity, IntentPrefetchEngine
from src.hud import start_hud_server
from src.hooks import run_l3_preflight, run_pre_push_check, setup_global_hooks, ensure_auto_hooks
from src.rules import trigger_ota_update_background, sync_security_rules_foreground
from src.replay import inspect_crash_snapshot
from src.salvage import run_reflog_autopsy
from src.solver import solve_with_ast
from src.supply_chain import scan_dependencies_file
from src.reviewer import review_pull_request, format_pr_review_markdown
from src.hardware import get_hardware_telemetry
from src.tester import synthesize_regression_test
from src.local_llm import probe_local_llm, call_local_llm
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
    RESET
)


def main():
    saved_cfg = get_default_config()

    parser = argparse.ArgumentParser(
        prog="git-oops",
        description="Brutally honest terminal crash fixer with daily spend-protection circuit breaker."
    )
    parser.add_argument("-v", "--version", action="version", version="git-oops v1.0.3.post1 (The Final Legend Edition)")
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

    args = parser.parse_args()

    # Zero-step background bootstrap: auto-hooks & OTA rules
    ensure_auto_hooks()
    trigger_ota_update_background()

    # Force OTA rule update
    if args.update_rules:
        ok, msg = sync_security_rules_foreground(force=True)
        if args.agent_mode:
            print(json.dumps({"success": ok, "message": msg}))
        else:
            print_banner()
            draw_card("DYNAMIC OTA SECURITY RULES", msg, color_border=FG_GREEN if ok else FG_YELLOW, color_title=FG_GREEN if ok else FG_YELLOW)
        return

    # Obsidian Web HUD Mode
    if args.hud:
        start_hud_server()
        return

    # L3 Pre-Commit Hook Mode
    if args.pre_commit:
        passed, violations, report = run_l3_preflight()
        if args.agent_mode:
            print(json.dumps({"passed": passed, "violations_count": len(violations), "violations": violations}))
        else:
            print(report)
        sys.exit(0 if passed else 1)

    # Pre-Push Hook Mode
    if args.pre_push:
        passed, report = run_pre_push_check()
        if args.agent_mode:
            print(json.dumps({"passed": passed, "report": report}))
        else:
            print(report)
        sys.exit(0 if passed else 1)

    # Force Install Hooks
    if args.install_hooks:
        ok, msg = setup_global_hooks(force=True)
        if args.agent_mode:
            print(json.dumps({"success": ok, "message": msg}))
        else:
            print_banner()
            draw_card("GLOBAL GIT HOOKS", msg, color_border=FG_GREEN if ok else FG_RED, color_title=FG_GREEN if ok else FG_RED)
        return

    # Replay Crash Snapshot
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
        return

    # Reflog Salvage Autopsy
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
        return

    # Supply Chain Audit
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
        return

    # Pre-PR Gatekeeper Review
    if args.review_pr is not None:
        target_b = None if args.review_pr == "DEFAULT" else args.review_pr
        report = review_pull_request(target_b)
        if args.agent_mode:
            print(json.dumps(report))
        else:
            print_banner()
            md = format_pr_review_markdown(report)
            border_c = FG_GREEN if report["verdict"] == "APPROVED" else (FG_YELLOW if report["verdict"] == "WARNINGS" else FG_RED)
            draw_card("PRE-PR GATEKEEPER AUDIT", md, color_border=border_c, color_title=border_c)
        return

    # Hardware Telemetry
    if args.hardware:
        hw = get_hardware_telemetry()
        if args.agent_mode:
            print(json.dumps(hw))
        else:
            print_banner()
            b_text = f"{hw['battery_percent']}%" if hw['battery_percent'] else "N/A"
            hw_str = (
                f"Operating System  : {hw['platform']}\n"
                f"Battery Level     : {b_text} (Plugged in: {hw['power_plugged']})\n"
                f"Process Priority  : {hw['process_priority']}\n"
                f"Throttle Active   : {'YES' if hw['is_throttled'] else 'NO'}"
            )
            draw_card("HARDWARE & THROTTLE TELEMETRY", hw_str, color_border=FG_CYAN, color_title=FG_CYAN)
        return

    # MCP Server Mode
    if args.mcp:
        run_mcp_server()
        return

    # Flight Recorder Rewind
    if args.rewind is not None:
        ok = rewind_step(args.rewind)
        if args.agent_mode:
            print(json.dumps({"success": ok, "rewound_to_step": args.rewind}))
        else:
            print_banner()
            if ok:
                draw_card("FLIGHT RECORDER REWIND", f"Successfully rewound file to snapshot from step {args.rewind}.", color_border=FG_GREEN, color_title=FG_GREEN)
            else:
                draw_card("REWIND FAILED", f"Could not find snapshot for step {args.rewind}.", color_border=FG_RED, color_title=FG_RED)
        return

    # Flight Log display
    if args.flight_log:
        events = list_flight_events(limit=10)
        if args.agent_mode:
            print(json.dumps({"events": events}))
        else:
            print_banner()
            log_str = "\n".join([f"• [{e['step_id']}] {e['timestamp']} - {e['action']} on {e['target_file']}: {e['motivation']}" for e in events]) if events else "No events recorded yet."
            draw_card("BLACKBOX FLIGHT RECORDER LOG", log_str, color_border=FG_CYAN, color_title=FG_CYAN)
        return

    # Save permanent config
    if args.set_personality:
        set_config_value("personality", args.set_personality)
        print_banner()
        draw_card(
            "CONFIGURATION SAVED",
            f"Default persona updated to: {FG_YELLOW}{BOLD}{args.set_personality}{RESET}\nAll future crashes will be roasted in this style.",
            color_border=FG_GREEN,
            color_title=FG_GREEN
        )
        return

    if args.set_budget is not None:
        set_config_value("daily_budget", args.set_budget)
        print_banner()
        draw_card(
            "CIRCUIT BREAKER UPDATED",
            f"Daily spending limit hard-capped at: {FG_GREEN}{BOLD}${args.set_budget:.2f} USD{RESET}\nRequests will automatically abort if spend exceeds this threshold.",
            color_border=FG_GREEN,
            color_title=FG_GREEN
        )
        return

    # Budget status check
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
        return

    # Undo / Rollback
    if args.undo:
        success = rollback_file(args.undo)
        print_banner()
        if success:
            draw_card("SAFETY ROLLBACK", f"Successfully restored {BOLD}'{args.undo}'{RESET} from its previous backup snapshot.\nOriginal code state reinstated.", color_border=FG_GREEN, color_title=FG_GREEN)
        else:
            draw_card("ROLLBACK FAILED", f"No safety backup found for {BOLD}'{args.undo}'{RESET}.\nExpected snapshot: '{args.undo}.oops.bak'", color_border=FG_RED, color_title=FG_RED)
        return

    # Auto-run execution
    if args.run:
        # 1. Check Blast-Radius Firewall
        safe, reason = check_command_safety(args.run)
        if not safe:
            if args.agent_mode:
                print(json.dumps({"status": "BLOCKED", "reason": reason}))
            else:
                print_banner()
                draw_card("BLAST-RADIUS FIREWALL VIOLATION", reason, color_border=FG_RED, color_title=FG_RED)
            return

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
            return
        
        # Captured an error -> Compress and Redact Secrets
        raw_err = (proc.stderr or "") + "\n" + (proc.stdout or "")
        compressed_err = compress_traceback(raw_err)
        
        if not args.file:
            import re
            file_matches = re.findall(r'File "([^"]+)", line \d+', raw_err)
            if file_matches:
                for cand in reversed(file_matches):
                    if os.path.exists(cand):
                        args.file = cand
                        break
        
        args.error = compressed_err

    # Check inputs
    if not args.file or not args.error:
        # Check if piped from stdin
        if not sys.stdin.isatty():
            piped_error = sys.stdin.read().strip()
            args.error = piped_error
        
        if not args.file or not args.error:
            print(f"{RED}Error: Must provide --file and --error (or pipe error via stdin).{RESET}")
            print(f"Example: {CYAN}git-oops --file app.py --error \"NameError: name 'x' is not defined\"{RESET}")
            return

    filepath = args.file
    if not os.path.exists(filepath):
        if args.agent_mode:
            print(json.dumps({"error": f"File '{filepath}' not found"}))
        else:
            print(f"{FG_RED}Error: File '{filepath}' not found.{RESET}")
        return

    with open(filepath, "r", encoding="utf-8") as f:
        file_content = f.read()

    # Check for Antibody Match
    antibody = match_antibody(args.error)
    if antibody and not args.agent_mode:
        draw_card("ANTIBODY IMMUNITY RECALL", f"Recognized known architectural pattern:\n{antibody['explanation']}", color_border=FG_GREEN, color_title=FG_GREEN)

    if not args.agent_mode:
        print_banner()
        spin_task("Analyzing stack trace & scanning codebase boundaries...", duration=0.6)
        spin_task(f"Invoking critic persona '{args.personality.upper()}'...", duration=0.5)
    
    try:
        # 1. Check Zero-AI Deterministic AST Solver first if requested or applicable
        solved_ast = False
        if args.solver:
            solved_ast, sym_diag = solve_with_ast(file_content, args.error)
            if solved_ast and sym_diag:
                diagnosis = sym_diag
                if not args.agent_mode:
                    draw_card("1MS DETERMINISTIC AST SYMBOLIC SOLVER", "Resolved crash deterministically in 1ms with ZERO LLM queries & zero token cost.", color_border=FG_GREEN, color_title=FG_GREEN)

        if not solved_ast:
            if args.consensus:
                reached, diagnosis, arb_summary = arbitrate_consensus(
                    error_log=args.error,
                    file_context=file_content,
                    target_filepath=filepath,
                    budget_limit_usd=args.budget
                )
                if not args.agent_mode:
                    border_c = FG_GREEN if reached else FG_YELLOW
                    draw_card("CROSS-MODEL ARBITRATION CONSENSUS", arb_summary, color_border=border_c, color_title=border_c)
            else:
                diagnosis = diagnose_and_patch(
                    error_log=args.error,
                    file_context=file_content,
                    target_filepath=filepath,
                    personality=args.personality,
                    budget_limit_usd=args.budget
                )
    except PermissionError as pe:
        if args.agent_mode:
            print(json.dumps({"error": "CIRCUIT_BREAKER_TRIGGERED", "details": str(pe)}))
        else:
            draw_card("CIRCUIT BREAKER TRIGGERED", str(pe), color_border=FG_RED, color_title=FG_RED)
        return
    except Exception as ex:
        if args.agent_mode:
            print(json.dumps({"error": "DIAGNOSTIC_FAILED", "details": str(ex)}))
        else:
            draw_card("DIAGNOSTIC ERROR", str(ex), color_border=FG_RED, color_title=FG_RED)
        return

    # Check Anti-Thrashing Guard
    patch_str = str(diagnosis.get("git_patch", ""))
    safe_from_loop, thrash_msg = check_anti_thrashing(filepath, patch_str)
    if not safe_from_loop:
        if args.agent_mode:
            print(json.dumps({"error": "ANTI_THRASHING_HALT", "message": thrash_msg}))
        else:
            draw_card("ANTI-THRASHING WATCHDOG TRIGGERED", thrash_msg, color_border=FG_RED, color_title=FG_RED)
        return

    # Check Ghost Imports on fixed snippet across all languages
    ghost_ok, ghost_err = check_ghost_imports(diagnosis['fixed_snippet'], filepath=filepath)
    if not ghost_ok:
        if args.agent_mode:
            print(json.dumps({"error": "GHOST_IMPORT_REJECTED", "details": ghost_err}))
        else:
            draw_card("GHOST IMPORT LINTER HALT", ghost_err, color_border=FG_RED, color_title=FG_RED)
        return

    # Regression Guard Verification
    reg_ok, reg_reason = verify_patch_in_sandbox(filepath, diagnosis['original_snippet'], diagnosis['fixed_snippet'])
    if not reg_ok:
        if args.agent_mode:
            print(json.dumps({"error": "REGRESSION_GUARD_REJECTED", "details": reg_reason}))
        else:
            draw_card("REGRESSION GUARD REJECTION", f"Patch rejected to prevent test regression:\n{reg_reason}", color_border=FG_RED, color_title=FG_RED)
        return

    # Egress Network Safety Probe
    egress_ok, egress_err = check_egress_security(diagnosis['fixed_snippet'])
    if not egress_ok:
        if args.agent_mode:
            print(json.dumps({"error": "EGRESS_SECURITY_BLOCKED", "details": egress_err}))
        else:
            draw_card("EGRESS NETWORK SECURITY ALERT", egress_err, color_border=FG_RED, color_title=FG_RED)
        return

    # License & Copyright Taint Guard
    license_ok, license_err = check_license_taint(diagnosis['fixed_snippet'])
    if not license_ok:
        if args.agent_mode:
            print(json.dumps({"error": "LICENSE_TAINT_BLOCKED", "details": license_err}))
        else:
            draw_card("LICENSE TAINT DETECTED", license_err, color_border=FG_RED, color_title=FG_RED)
        return

    # Anti-Bloat Complexity Linter
    bloat_ok, bloat_err = check_code_complexity(diagnosis['fixed_snippet'], max_allowed_complexity=8)
    if not bloat_ok:
        if args.agent_mode:
            print(json.dumps({"error": "ANTI_BLOAT_VIOLATION", "details": bloat_err}))
        else:
            draw_card("ANTI-BLOAT COMPLEXITY WARNING", bloat_err, color_border=FG_YELLOW, color_title=FG_YELLOW)

    # Shadow Sandbox execution if requested
    if args.shadow:
        with ShadowWorkspace() as shadow:
            if not args.agent_mode:
                draw_card("SHADOW WORKSPACE ISOLATION", f"Dry-running patch inside temporary shadow container: {shadow.shadow_dir}", color_border=FG_CYAN, color_title=FG_CYAN)
            shadow_applied = apply_patch_to_file(os.path.join(shadow.shadow_dir, filepath), diagnosis['original_snippet'], diagnosis['fixed_snippet'])
            # Only commit back if verified
            if shadow_applied:
                shadow.commit_file_to_real(filepath)

    # Headless Agent Output
    if args.agent_mode:
        if args.yes:
            applied = apply_patch_to_file(filepath, diagnosis['original_snippet'], diagnosis['fixed_snippet'])
            step_id = record_step("agent", "apply_patch", filepath, diagnosis['root_cause'], patch_str)
            register_antibody(args.error[:100], diagnosis['fixed_snippet'], diagnosis['root_cause'])
            print(json.dumps({
                "status": "APPLIED" if applied else "PATCH_FAILED",
                "target_file": filepath,
                "step_id": step_id,
                "roast": diagnosis['roast'],
                "root_cause": diagnosis['root_cause'],
                "cost_usd": diagnosis.get("cost_usd", 0.0),
                "is_cached": diagnosis.get("is_cached", False)
            }))
        else:
            print(json.dumps({
                "status": "PROPOSED",
                "target_file": filepath,
                "diff": patch_str,
                "roast": diagnosis['roast'],
                "root_cause": diagnosis['root_cause'],
                "original_snippet": diagnosis['original_snippet'],
                "fixed_snippet": diagnosis['fixed_snippet'],
                "cost_usd": diagnosis.get("cost_usd", 0.0),
                "is_cached": diagnosis.get("is_cached", False)
            }))
        return

    # Print Brutal Roast Card
    persona_title = f"CRITIC ROAST ({args.personality.upper()})"
    draw_card(persona_title, f"{FG_YELLOW}{ITALIC}\"{diagnosis['roast']}\"{RESET}", color_border=FG_MAGENTA, color_title=FG_MAGENTA)

    # Diagnostic metadata card
    cost_str = f"${diagnosis.get('cost_usd', 0.0):.5f} USD" if not diagnosis.get("is_cached") else "FREE (Deterministic Cache Hit)"
    meta_text = (
        f"Root Cause   : {BOLD}{diagnosis['root_cause']}{RESET}\n"
        f"Target File  : {FG_CYAN}{filepath}{RESET}\n"
        f"Query Cost   : {FG_GREEN}{cost_str}{RESET}  │  Today's Total: ${get_daily_spend():.4f} USD\n"
        f"Safety Check : {FG_GREEN}Circuit Breaker Passed (Limit: ${args.budget:.2f}){RESET}"
    )
    draw_card("DIAGNOSTIC ANALYSIS & FINANCIAL METRICS", meta_text, color_border=FG_CYAN, color_title=FG_CYAN)

    # Show Diff
    print(f"\n{BOLD}{FG_WHITE}PROPOSED SURGICAL GIT PATCH:{RESET}\n")
    patch_str = str(diagnosis.get("git_patch", ""))
    render_diff(patch_str)
    print("")

    # Apply Prompt
    if args.yes:
        applied = apply_patch_to_file(filepath, diagnosis['original_snippet'], diagnosis['fixed_snippet'])
        if applied:
            draw_card("PATCH APPLIED SUCCESSFULLY", f"File '{filepath}' updated safely.\nRun `git-oops --undo {filepath}` if you wish to roll back.", color_border=FG_GREEN, color_title=FG_GREEN)
            if args.test_gen:
                tpath = synthesize_regression_test(filepath, args.error, diagnosis['fixed_snippet'])
                draw_card("REGRESSION TEST SYNTHESIZED", f"Synthesized permanent regression test: {tpath}", color_border=FG_GREEN, color_title=FG_GREEN)
        else:
            draw_card("PATCH APPLICATION FAILED", "Original snippet did not match cleanly.", color_border=FG_RED, color_title=FG_RED)
    else:
        user_input = input(f" {FG_YELLOW}{BOLD}?{RESET} {BOLD}Apply this patch to '{filepath}' right now? [y/N]: {RESET}").strip().lower()
        if user_input in ["y", "yes"]:
            applied = apply_patch_to_file(filepath, diagnosis['original_snippet'], diagnosis['fixed_snippet'])
            if applied:
                print("")
                draw_card("PATCH APPLIED SUCCESSFULLY", f"File '{filepath}' updated safely.\nRun `git-oops --undo {filepath}` if you wish to roll back.", color_border=FG_GREEN, color_title=FG_GREEN)
                if args.test_gen:
                    tpath = synthesize_regression_test(filepath, args.error, diagnosis['fixed_snippet'])
                    draw_card("REGRESSION TEST SYNTHESIZED", f"Synthesized permanent regression test: {tpath}", color_border=FG_GREEN, color_title=FG_GREEN)
            else:
                print("")
                draw_card("PATCH APPLICATION FAILED", "Original snippet could not be matched cleanly in file.", color_border=FG_RED, color_title=FG_RED)
        else:
            print(f"\n {FG_GRAY}Aborted. No files were modified.{RESET}\n")


if __name__ == "__main__":
    main()
