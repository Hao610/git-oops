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

from src.circuit_breaker import get_daily_spend
from src.engine import diagnose_and_patch, apply_patch_to_file, rollback_file

# ANSI styling
BOLD = "\033[1m"
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
MAGENTA = "\033[95m"
CYAN = "\033[96m"
RESET = "\033[0m"


def main():
    parser = argparse.ArgumentParser(
        prog="git-oops",
        description="Brutally honest terminal crash fixer with daily spend-protection circuit breaker."
    )
    parser.add_argument("-f", "--file", help="Path to the file that crashed", default=None)
    parser.add_argument("-e", "--error", help="Error message or traceback string", default=None)
    parser.add_argument("-b", "--budget", help="Daily API spend ceiling in USD (default: $1.00)", type=float, default=1.0)
    parser.add_argument("-p", "--personality", help="Roast persona: 'staff', 'linus', 'ramsay', or 'passive_aggressive'", default="staff", choices=["staff", "linus", "ramsay", "passive_aggressive"])
    parser.add_argument("-y", "--yes", help="Auto-apply patch without interactive prompt", action="store_true")
    parser.add_argument("--undo", help="Roll back the last applied patch on target file", default=None)
    parser.add_argument("--run", help="Execute a command and auto-catch its crash (e.g. --run 'python app.py')", default=None)
    parser.add_argument("--status", help="Show today's accumulated API spend", action="store_true")

    args = parser.parse_args()

    # Budget status check
    if args.status:
        spent = get_daily_spend()
        print(f"\n{BOLD}{CYAN}🛡️  [GIT-OOPS CIRCUIT BREAKER STATUS]{RESET}")
        print(f"Today's Accumulated Spend : {GREEN}${spent:.5f} USD{RESET}")
        print(f"Safety Threshold          : {YELLOW}${args.budget:.2f} USD{RESET}\n")
        return

    # Undo / Rollback
    if args.undo:
        success = rollback_file(args.undo)
        if success:
            print(f"\n{GREEN}⏪ [ROLLBACK SUCCESS] Restored '{args.undo}' from previous backup.{RESET}\n")
        else:
            print(f"\n{RED}❌ [ROLLBACK FAILED] No backup found for '{args.undo}' (expected '{args.undo}.oops.bak').{RESET}\n")
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
        print(f"{RED}Error: File '{filepath}' not found.{RESET}")
        return

    with open(filepath, "r", encoding="utf-8") as f:
        file_content = f.read()

    print(f"\n{BOLD}{MAGENTA}⚡ [GIT-OOPS] Analyzing crash & invoking staff-level critic...{RESET}")
    
    try:
        diagnosis = diagnose_and_patch(
            error_log=args.error,
            file_context=file_content,
            target_filepath=filepath,
            personality=args.personality,
            budget_limit_usd=args.budget
        )
    except PermissionError as pe:
        print(f"\n{RED}{BOLD}{pe}{RESET}\n")
        return
    except Exception as ex:
        print(f"\n{RED}Diagnostic failed: {ex}{RESET}\n")
        return

    # Print Brutal Roast
    print(f"\n{BOLD}{RED}💀 THE ROAST:{RESET}")
    print(f"{YELLOW}\"{diagnosis['roast']}\"{RESET}\n")

    print(f"{BOLD}{CYAN}🔍 ROOT CAUSE:{RESET} {diagnosis['root_cause']}")
    
    # Financial metrics
    cost_str = f"${diagnosis.get('cost_usd', 0.0):.5f}" if not diagnosis.get("is_cached") else "FREE (Cache Hit)"
    print(f"{BOLD}💰 COST INCURRED:{RESET} {GREEN}{cost_str}{RESET} (Total today: ${get_daily_spend():.4f})")

    # Show Diff
    print(f"\n{BOLD}{GREEN}📝 PROPOSED GIT PATCH:{RESET}")
    patch_str = str(diagnosis.get("git_patch", ""))
    print(f"```diff\n{patch_str}\n```\n")

    # Apply Prompt
    if args.yes:
        applied = apply_patch_to_file(filepath, diagnosis['original_snippet'], diagnosis['fixed_snippet'])
        if applied:
            print(f"{GREEN}✅ Patch successfully written to {filepath}!{RESET}\n")
        else:
            print(f"{YELLOW}⚠️ Could not auto-apply: snippet did not match cleanly.{RESET}\n")
    else:
        user_input = input(f"{BOLD}Apply this patch to '{filepath}' right now? [y/N]: {RESET}").strip().lower()
        if user_input in ["y", "yes"]:
            applied = apply_patch_to_file(filepath, diagnosis['original_snippet'], diagnosis['fixed_snippet'])
            if applied:
                print(f"\n{GREEN}✅ Patch applied! Run your script again.{RESET}\n")
            else:
                print(f"\n{YELLOW}⚠️ Patch not applied: Original snippet could not be matched.{RESET}\n")
        else:
            print(f"\n{BLUE}Aborted. No files were modified.{RESET}\n")


if __name__ == "__main__":
    main()
