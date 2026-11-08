"""
Git-Oops High-Fidelity Terminal UI Renderer
Zero-dependency, pure ANSI + Unicode box drawing.
Produces Apple/Vercel/Stripe-tier CLI aesthetic.
"""

import sys
import time
import shutil

# Color & Style constants
RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
ITALIC = "\033[3m"
UNDERLINE = "\033[4m"

# Foreground 24-bit Truecolor & ANSI
FG_RED = "\033[38;5;203m"
FG_GREEN = "\033[38;5;120m"
FG_YELLOW = "\033[38;5;221m"
FG_BLUE = "\033[38;5;75m"
FG_MAGENTA = "\033[38;5;176m"
FG_CYAN = "\033[38;5;86m"
FG_WHITE = "\033[38;5;255m"
FG_GRAY = "\033[38;5;244m"
FG_DARK = "\033[38;5;238m"

# Backgrounds
BG_RED = "\033[48;5;52m"
BG_GREEN = "\033[48;5;22m"
BG_DARK = "\033[48;5;236m"

LOGO = f"""{FG_MAGENTA}{BOLD}
         _ _                             
   __ _ (_) |_        ___   ___  _ __  ___ 
  / _` || | __|_____ / _ \\ / _ \\| '_ \\/ __|
 | (_| || | |_|_____| (_) | (_) | |_) \\__ \\
  \\__, |/ |\\__|      \\___/ \\___/| .__/|___/
  |___/__/                      |_|        
{RESET}{FG_GRAY}   ⚡ Automated Crash-to-Patch Synthesizer │ Staff Critic │ Circuit Breaker{RESET}
"""


def print_banner():
    print(LOGO)


import re
import textwrap

ANSI_ESCAPE = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')

def strip_ansi(text: str) -> str:
    """Returns the visible string length excluding ANSI color escape sequences."""
    return ANSI_ESCAPE.sub('', text)


def draw_card(title: str, content: str, color_border: str = FG_CYAN, color_title: str = FG_WHITE, width: int = 76):
    """Renders sleek rounded card UI with exact ANSI-aware line wrapping."""
    term_width = shutil.get_terminal_size((80, 24)).columns
    box_width = min(width, max(50, term_width - 4))
    inner_width = box_width - 6

    visible_title_len = len(strip_ansi(title))
    dashes_len = max(2, box_width - visible_title_len - 6)
    top_border = f"{color_border}╭─ {color_title}{BOLD}{title}{RESET} {color_border}{'─' * dashes_len}╮{RESET}"
    bottom_border = f"{color_border}╰{'─' * (box_width - 2)}╯{RESET}"

    print(top_border)
    for raw_line in content.splitlines():
        # Strip trailing return chars
        raw_line = raw_line.rstrip()
        vis_len = len(strip_ansi(raw_line))
        if vis_len <= inner_width:
            padding = " " * (inner_width - vis_len)
            print(f"{color_border}│{RESET}  {raw_line}{padding}  {color_border}│{RESET}")
        else:
            # Word-wrap preserving styles
            plain_line = strip_ansi(raw_line)
            wrapped = textwrap.wrap(raw_line, width=inner_width, break_long_words=True)
            for w in wrapped:
                w_vis = len(strip_ansi(w))
                padding = " " * (inner_width - w_vis)
                print(f"{color_border}│{RESET}  {w}{padding}  {color_border}│{RESET}")
    print(bottom_border)


def render_diff(patch_str: str):
    """Renders GitHub/GitLab-style colored unified diff."""
    lines = patch_str.strip().splitlines()
    for line in lines:
        if line.startswith("---") or line.startswith("+++"):
            print(f"{BOLD}{FG_GRAY}{line}{RESET}")
        elif line.startswith("@@"):
            print(f"{FG_CYAN}{BOLD}{line}{RESET}")
        elif line.startswith("+"):
            print(f"{BG_GREEN}{FG_GREEN}{BOLD}{line}{RESET}")
        elif line.startswith("-"):
            print(f"{BG_RED}{FG_RED}{BOLD}{line}{RESET}")
        else:
            print(f"{FG_GRAY}  {line}{RESET}")


def spin_task(msg: str, duration: float = 0.8):
    """Renders slick CLI radar spinner."""
    frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    start = time.time()
    i = 0
    sys.stdout.write("\n")
    while time.time() - start < duration:
        frame = frames[i % len(frames)]
        sys.stdout.write(f"\r  {FG_CYAN}{BOLD}{frame}{RESET}  {FG_WHITE}{msg}{RESET}   ")
        sys.stdout.flush()
        time.sleep(0.08)
        i += 1
    sys.stdout.write(f"\r  {FG_GREEN}{BOLD}✔{RESET}  {FG_WHITE}{msg}{RESET}   \n\n")
    sys.stdout.flush()
