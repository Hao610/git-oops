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
    parser.add_argument("-f", "--file", help="Path to the file that crashed", default=None)
    parser.add_argument("-e", "--error", help="Error message or traceback string", default=None)
    parser.add_argument("-b", "--budget", help="Daily API spend ceiling in USD (default: $1.00)", type=float, default=saved_cfg.get("daily_budget", 1.0))
    parser.add_argument("-p", "--personality", help="Roast persona: 'staff', 'kernel', 'chef', or 'passive_aggressive'", default=saved_cfg.get("personality", "staff"), choices=["staff", "kernel", "chef", "passive_aggressive"])
    parser.add_argument("--set-personality", help="Permanently save default roast persona", choices=["staff", "kernel", "chef", "passive_aggressive"])
    parser.add_argument("--set-budget", help="Permanently save default daily spend budget in USD", type=float)
    parser.add_argument("-y", "--yes", help="Auto-apply patch without interactive prompt", action="store_true")
    parser.add_argument("--undo", help="Roll back the last applied patch on target file", default=None)
    parser.add_argument("--run", help="Execute a command and auto-catch its crash (e.g. --run 'python app.py')", default=None)
    parser.add_argument("--status", help="Show today's accumulated API spend", action="store_true")

    args = parser.parse_args()

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
        print(f"\n{BOLD}{CYAN}🚀 [GIT-OOPS RUNNER] Executing: {args.run}{RESET}\n")
        proc = subprocess.run(args.run, shell=True, capture_output=True, text=True, encoding="utf-8", errors="replace")
        if proc.returncode == 0:
            print(proc.stdout)
            print(f"{GREEN}✨ Command executed successfully without errors!{RESET}\n")
            return
        
        # Captured an error
        err_output = (proc.stderr or "") + "\n" + (proc.stdout or "")
        print(f"{RED}💥 Crash detected! (Exit code {proc.returncode}){RESET}")
        
        # If user didn't specify file, try to extract it from traceback
        if not args.file:
            import re
            file_matches = re.findall(r'File "([^"]+)", line \d+', err_output)
            if file_matches:
                # pick the last local file mentioned
                for cand in reversed(file_matches):
                    if os.path.exists(cand):
                        args.file = cand
                        break
        
        args.error = err_output.strip()
        if not args.file:
            print(f"{YELLOW}Could not automatically determine crashed file. Please provide --file.{RESET}")

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
        print(f"{FG_RED}Error: File '{filepath}' not found.{RESET}")
        return

    with open(filepath, "r", encoding="utf-8") as f:
        file_content = f.read()

    print_banner()
    spin_task("Analyzing stack trace & scanning codebase boundaries...", duration=0.6)
    spin_task(f"Invoking critic persona '{args.personality.upper()}'...", duration=0.5)
    
    try:
        diagnosis = diagnose_and_patch(
            error_log=args.error,
            file_context=file_content,
            target_filepath=filepath,
            personality=args.personality,
            budget_limit_usd=args.budget
        )
    except PermissionError as pe:
        draw_card("CIRCUIT BREAKER TRIGGERED", str(pe), color_border=FG_RED, color_title=FG_RED)
        return
    except Exception as ex:
        draw_card("DIAGNOSTIC ERROR", str(ex), color_border=FG_RED, color_title=FG_RED)
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
        else:
            draw_card("PATCH APPLICATION FAILED", "Original snippet did not match cleanly.", color_border=FG_RED, color_title=FG_RED)
    else:
        user_input = input(f" {FG_YELLOW}{BOLD}?{RESET} {BOLD}Apply this patch to '{filepath}' right now? [y/N]: {RESET}").strip().lower()
        if user_input in ["y", "yes"]:
            applied = apply_patch_to_file(filepath, diagnosis['original_snippet'], diagnosis['fixed_snippet'])
            if applied:
                print("")
                draw_card("PATCH APPLIED SUCCESSFULLY", f"File '{filepath}' updated safely.\nRun `git-oops --undo {filepath}` if you wish to roll back.", color_border=FG_GREEN, color_title=FG_GREEN)
            else:
                print("")
                draw_card("PATCH APPLICATION FAILED", "Original snippet could not be matched cleanly in file.", color_border=FG_RED, color_title=FG_RED)
        else:
            print(f"\n {FG_GRAY}Aborted. No files were modified.{RESET}\n")


if __name__ == "__main__":
    main()
