# 🆘 Git-Oops Complete Manual: Beginner to Agent Master

Welcome to the definitive manual for **`git-oops`** — the Dual-Mode Terminal Crash Fixer and Autonomous AI Agent Safety Harness.

---

## 🐣 Absolute Beginner Quickstart (Zero-Confusion Guide)

If you are a complete beginner or don't know how to install CLIs and MCP servers, **follow these 3 simple steps**:

### Step 1: Install `git-oops` with 1 command
Open your terminal (PowerShell, Command Prompt, or Mac/Linux Terminal) and run:

```bash
git clone https://github.com/Hao610/git-oops.git
cd git-oops
pip install -e .
```
*(That's it! `git-oops` is now a global command on your computer.)*

---

### Step 2: Use it as a Human (Fix a broken file)
Whenever a script crashes:
```bash
git-oops --file broken.py --error "KeyError: 'user_id'"
```
- It roasts your code with funny commentary.
- It displays a high-fidelity visual card with a unified Git patch.
- Press **`y`** to apply the fix immediately to your file!
- Regret it? Type **`git-oops --undo broken.py`** to instantly restore your backup!

---

### Step 3: How to connect `git-oops` to Claude Desktop or Cursor (MCP Setup)

You don't need any networking knowledge. Modern AI assistants support **MCP (Model Context Protocol)**. Here is how to hook it up in 30 seconds:

#### For Claude Desktop:
1. Open Claude Desktop Settings ➔ **Developer** ➔ **Edit Config**.
2. Open your `claude_desktop_config.json` and paste this block:

```json
{
  "mcpServers": {
    "git-oops": {
      "command": "git-oops",
      "args": ["--mcp"]
    }
  }
}
```
3. Restart Claude Desktop. You will see a small hammer icon 🛠️ showing `git_oops_diagnose` and `git_oops_safe_exec`! Claude can now use your terminal tools safely!

#### For Antigravity (Google AGY):
In your workspace or global config, add to your MCP server configuration:
```json
{
  "mcpServers": {
    "git-oops": {
      "command": "git-oops",
      "args": ["--mcp"]
    }
  }
}
```
Now Antigravity subagents and autonomous tasks will automatically route code fixes and terminal commands through `git-oops`'s safety harness.

#### For OpenAI Codex / Qoder / Copilot CLI / Aider / Devin:
These tools execute shell commands in a sub-process. You don't even need to configure MCP!
Simply instruct the agent or set its system prompt / rule to:
> *"Whenever you encounter a crash or want to apply a patch safely, execute: `git-oops --agent --file <path> --error \"<error>\" --yes`"*

The agent will receive a pristine, single-turn JSON payload:
```json
{
  "status": "APPLIED",
  "target_file": "app.py",
  "step_id": 1731174000,
  "roast": "...",
  "root_cause": "KeyError on missing dict key",
  "cost_usd": 0.00012
}
```
Zero ANSI garbage, 100% reliable programmatic parsing across any autonomous agent!

---

## ⚡ Comprehensive Command Sheet

### 🧑‍💻 Human Mode (Interactive & Colorful)
| Task | Command | Description |
| :--- | :--- | :--- |
| **Fix crash directly** | `git-oops --file app.py --error "..."` | Analyzes crash, roasts code, displays Git diff. |
| **Run command & intercept crash**| `git-oops --run "python app.py"` | Executes command live, catches crash, and auto-fixes. |
| **Undo last patch** | `git-oops --undo app.py` | Restores the file from its `.oops.bak` snapshot. |
| **Check today's budget** | `git-oops --status` | Shows today's spend down to 5 decimals. |
| **Set daily spend budget** | `git-oops --set-budget 2.50` | Hard-caps API spending at $2.50 USD. |
| **Set roast persona** | `git-oops --set-personality chef` | Locks in `chef`, `staff`, `kernel`, or `passive_aggressive`. |

### 🤖 Autonomous Agent Mode (Headless JSON & MCP)
| Task | Command | Description |
| :--- | :--- | :--- |
| **Machine-Readable Mode** | `git-oops --agent --file app.py --error "..." --yes` | Emits pure JSON without ANSI colors for AI parsing. |
| **Start MCP Server** | `git-oops --mcp` | Listens on stdio (JSON-RPC 2.0) for Claude/Cursor. |
| **Shadow Sandbox Isolation** | `git-oops --shadow --file app.py --error "..."` | Dry-runs patch in an isolated temporary clone directory. |
| **Dual-Model Consensus** | `git-oops --consensus --file app.py --error "..."` | Dispatches to two models; only patches if both agree. |
| **View Flight Recorder** | `git-oops --flight-log` | Displays audit log of recent agent decisions. |
| **Rewind Step** | `git-oops --rewind <step_id>` | Restores file state back to a previous snapshot step. |

---

## 🛡️ The Complete 20-Pillar Defense Matrix

1. **Dual-Mode Engine**: Human visual UI or headless agent JSON.
2. **Native MCP Server**: JSON-RPC 2.0 stdio server for modern AI tools.
3. **Blast-Radius Firewall**: Blocks `rm -rf`, `force-push`, and disk wiping.
4. **Supply-Chain Shield**: Blocks hallucinated and typosquatted package traps (`reqeusts`).
5. **Egress Sniffer**: Blocks patches containing unauthorized phone-home or data exfiltration calls.
6. **Multi-Agent Mutex**: Cooperative file locks preventing concurrent agents from corrupting files.
7. **Shadow Workspace**: Ephemeral clone sandbox; commits back only upon full validation.
8. **Anti-Thrashing Watchdog**: Halts agent edit-revert loops (> 3 times).
9. **Regression Guard**: Runs project unit tests in sandbox before modifying source code.
10. **AST Ghost-Import Linter**: 0 ms syntax scan blocking hallucinated non-existent modules.
11. **Cross-Model Consensus**: Dual-model arbitration eliminating single-model hallucinations.
12. **Anti-Bloat Complexity Slasher**: Rejects patches that inflate cyclomatic complexity into spaghetti code.
13. **License Taint Shield**: Blocks viral GPL/AGPL copy-paste contamination.
14. **Context Log Squeezer**: Compresses 5,000-line stack traces to 20 focused lines.
15. **Secret Redactor**: Auto-masks API keys and tokens (`<REDACTED_SECRET>`).
16. **Intent Prefetch Engine**: Markov-chain prediction prefetching next-step responses.
17. **Flight Recorder**: Full audit logging of agent intentions, tools, and snapshots.
18. **Time-Machine Rewind**: 1-click snapshot restoration to any previous step.
19. **Antibody Immunity DB**: Persistent cross-session memory ledger of verified architecture patterns.
20. **Anti-Bit-Rot Evolution**: Auto-migrates schema and models to prevent code aging over decades.

---

## ❓ FAQ & Troubleshooting

### Q1: `git-oops : The term 'git-oops' is not recognized`
Run `pip install -e .` inside the repository directory, or run with `python -m src.cli` directly.

### Q2: I don't have an API key. Can I still use it?
Yes! `git-oops` includes a deterministic offline diagnostic critic. You can test all 20 safety features, UI cards, and diff applications completely offline without an internet connection or credit card.

### Q3: What is the privacy policy regarding my code and files?
`git-oops` operates under a strict **100% Local & Zero-Telemetry Guarantee**:
- No user analytics, telemetry tracking, or background pings are ever dispatched.
- All 20 defense modules (firewall, squeezer, AST linter, shadow workspace, etc.) run locally on your device.
- All audit data (flight recorder, snapshots, and antibody patterns) is stored exclusively on your local disk at `~/.git_oops/`.
- Secret redaction automatically masks all API keys and bearer credentials before any prompt reaches an LLM.

### Q4: What happens if an AI Agent proposes a bad patch that breaks my code?
You have two immediate safety nets:
1. **Interactive Prompt**: In human mode, `git-oops` asks `[y/N]` before applying any patch.
2. **Instant 1-Second Undo**: If a patch was applied, run `git-oops --undo <filepath>` to instantly revert to the pre-patch backup snapshot.
3. **Flight Rewind**: In autonomous agent mode, run `git-oops --rewind <step_id>` to restore any past snapshot.

### Q5: How do I change my daily API spending budget?
You can temporarily adjust it with the `--budget` flag:
```bash
git-oops --file app.py --error "..." --budget 2.50
```
Or permanently save your budget limit so it applies to all future runs:
```bash
git-oops --set-budget 3.00
```

### Q6: How does the Anti-Thrashing Watchdog distinguish normal edits from infinite loops?
`git-oops` calculates the SHA-256 cryptographic digest of every patch proposed per file. If an agent proposes the exact same patch or an immediate reverse toggle 3 times in a row, `git-oops` halts execution with `ANTI_THRASHING_HALT` to break the rabbit hole.

### Q7: Can I use `git-oops` with other programming languages (JavaScript, Go, Rust)?
Yes! While the AST Ghost-Import linter is currently specialized for Python, all other 19 defense modules — including the Blast-Radius Firewall, Context Log Squeezer, Secret Redactor, Shadow Workspace, Anti-Thrashing Watchdog, and Native MCP Server — work seamlessly across any language stack.

### Q8: Where are local configurations and cache files stored?
All files are housed strictly inside your operating system's local user home directory:
- Configuration: `~/.git_oops/config.json`
- Spend Ledger: `~/.git_oops/spend_ledger.json`
- Deterministic Cache: `~/.git_oops/cache.json`
- Blackbox Flight Events: `~/.git_oops/memory/flight_recorder.jsonl`
- Antibody DB: `~/.git_oops/memory/antibodies.json`

### Q9: Does `git-oops` require internet access?
No. Aside from optional cloud REST calls to Gemini/Claude when you provide an API key, the entire core harness (firewall, squeezer, watchdog, linter, sandbox, and local cache) operates completely air-gapped without an internet connection.

### Q10: How do I run `git-oops` in CI/CD pipelines (GitHub Actions, GitLab CI)?
Pass the `--agent` (or `--json`) flag along with `--yes` to auto-apply validated fixes without prompting:
```bash
git-oops --agent --file src/main.py --error "$ERROR_LOG" --yes
```
It returns standard Unix exit codes (`0` for success, non-zero for blocked/failures) with clean JSON for CI loggers.
