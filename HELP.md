# 🆘 Git-Oops Help & Troubleshooting Manual

Welcome to the definitive guide and troubleshooting reference for **`git-oops`**.

---

## ⚡ Quick Command Reference Sheet

| Task | Command | Description |
| :--- | :--- | :--- |
| **Fix crash directly** | `git-oops --file app.py --error "KeyError: 'id'"` | Analyzes crash, roasts the bug, and generates a 1-click patch. |
| **Live command runner** | `git-oops --run "python app.py"` | Executes your script, intercepts any crash live, and diagnoses immediately. |
| **Check today's budget** | `git-oops --status` | Shows accumulated USD spend, threshold, and remaining safe headroom. |
| **Undo / Rollback patch** | `git-oops --undo app.py` | Instantly reverts the file to its pre-patch state. |
| **Set toxic persona** | `git-oops --personality [mode]` | One-time persona (`staff`, `kernel`, `chef`, `passive_aggressive`). |
| **Permanently save persona**| `git-oops --set-personality chef` | Saves preferred persona permanently to `~/.git_oops/config.json`. |
| **Set daily spend limit** | `git-oops --set-budget 2.50` | Hard-caps maximum daily API spend in USD. |
| **Auto-apply patch** | `git-oops --file app.py --error "..." --yes` | Applies patch directly without interactive confirmation prompt. |

---

## 🎭 Roast Personas Explained

`git-oops` offers 4 distinct personalities with zero polite filler:

1. **`staff` (Default)**: Cold, cynical, technically unassailable Principal/Staff Engineer. Pointed critique on architectural laziness.
2. **`kernel`**: Explosive, furious OS kernel maintainer. Zero tolerance for memory leaks, invalid map access, or sloppy paradigms.
3. **`chef`**: High-decibel kitchen tirade. *"THIS CODE IS RAW! AN IDIOT SANDWICH!"*
4. **`passive_aggressive`**: Toxic corporate Slack coworker. *"Per my previous 15 code reviews... hope you enjoy on-call duty tonight 😊"*

---

## 🛡️ Circuit Breaker & Spend Protection

### How does the circuit breaker work?
Every outgoing API request calculates token volume and records exact costs in `~/.git_oops/spend_ledger.json`. 
If cumulative spend today meets or exceeds your threshold (default: `$1.00 USD`), the engine raises `PermissionError` and physically aborts requests to prevent surprise cloud bills.

### What is the deterministic cache?
Duplicate queries with identical file content and error tracebacks generate an exact SHA-256 hash key stored in `~/.git_oops/cache.json`.
* **Cost**: $0.00000 USD
* **Latency**: 0 ms
* **Internet connection**: Not required

---

## 🔧 Frequently Asked Questions & Troubleshooting

### Q1: `Error: File 'app.py' not found`
* **Cause**: You provided a relative file path that does not exist in your current terminal working directory.
* **Fix**: Ensure your shell is in the repository root or provide the full absolute path:
  ```bash
  git-oops --file D:\MyProject\app.py --error "ValueError: invalid literal"
  ```

### Q2: I pressed `[y]` but my code broke even further. How do I revert?
* **Fix**: Run the instant undo command:
  ```bash
  git-oops --undo app.py
  ```
  `git-oops` creates a protected `.oops.bak` snapshot before modifying any file on disk.

### Q3: How do I use `git-oops` offline without an API key?
* If `GEMINI_API_KEY` is not found in your environment, `git-oops` automatically switches to the built-in offline simulation critic, allowing full evaluation without internet or cloud credentials.

### Q4: How do I configure my API Key?
* **Linux / macOS**:
  ```bash
  export GEMINI_API_KEY="AIzaSy..."
  ```
* **Windows PowerShell**:
  ```powershell
  $env:GEMINI_API_KEY="AIzaSy..."
  ```
* **Windows Command Prompt (CMD)**:
  ```cmd
  set GEMINI_API_KEY=AIzaSy...
  ```

---

## 📄 Storage Paths & Privacy
All persistent files are stored strictly locally in your user home directory:
* **Config**: `~/.git_oops/config.json`
* **Cost Ledger**: `~/.git_oops/spend_ledger.json`
* **Response Cache**: `~/.git_oops/cache.json`

No telemetry, personal data, or codebase analytics are ever collected or transmitted.
