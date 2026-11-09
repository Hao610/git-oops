<div align="center">

# ⚡ git-oops

### *The Dual-Mode Terminal Crash Fixer & Autonomous AI Agent Safety Harness.*
**Human Mode: Roasted by a Staff Engineer │ Agent Mode: The Headless Shield for Coding Agents**

<p align="center">
  <img src="assets/readme-hero.jpg" alt="git-oops Hero Banner" width="850" style="border-radius: 10px; margin: 15px 0;" />
</p>

[![CI Suite](https://github.com/Hao610/git-oops/actions/workflows/ci.yml/badge.svg)](https://github.com/Hao610/git-oops/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/Python-3.9%20%7C%203.10%20%7C%203.11%20%7C%203.12%20%7C%203.13-blue?logo=python)](https://www.python.org/)
[![Zero-Dependency](https://img.shields.io/badge/Dependencies-Zero%20Heavy%20C%20Exts-success)]()
[![MCP-Ready](https://img.shields.io/badge/MCP-Native%20Server%20Ready-purple)]()
[![Spend-Protection](https://img.shields.io/badge/Wallet-Circuit%20Breaker%20Protected-orange)]()

</div>

---

## 😤 Why git-oops?

### For Humans:
Your script crashes with a 50-line traceback. You're exhausted, and ChatGPT gives you a polite 6-paragraph email instead of a 2-line fix.
`git-oops` roasts your sloppy code with razor-sharp wit and applies a surgical 1-click git patch directly in your terminal.

### For AI Coding Agents (Claude, Cursor, Windsurf, Codex, Devin):
Modern autonomous coding agents face catastrophic failure modes:
1. **Context Bloat**: Multi-thousand line terminal dumps overflow agent context windows.
2. **Infinite Thrashing**: Agents get trapped in loops editing and reverting the same code.
3. **Ghost Hallucinations**: Agents import non-existent libraries or fall into typosquatted package traps.
4. **Blast-Radius Disasters**: Agents accidentally execute `rm -rf` or destructive force-pushes.

**`git-oops` provides the missing runtime safety harness that shields your repository, your sanity, and your wallet.**

---

## ⚡ The Dual-Mode Architecture

```text
                        [ Terminal Crash / Agent Execution ]
                                          │
                   ┌──────────────────────┴──────────────────────┐
                   ▼                                             ▼
        [ 🧑‍💻 HUMAN MODE ]                                [ 🤖 AGENT MODE ]
  • High-Fidelity Rounded Cards                   • Clean Machine-Readable JSON
  • Caustic Critic Roasts (Staff/Chef)            • 90% Context Log Squeezer & Redactor
  • Interactive [y/N] Patch Confirmation          • Blast-Radius Firewall & AST Linter
  • Instant `--undo` Reversion                    • Anti-Thrashing Watchdog & Mutex
                   │                                             │
                   └──────────────────────┬──────────────────────┘
                                          ▼
                         [ 🛡️ SHA-256 Cache & Circuit Breaker ]
                         [ 🔌 Native Model Context Protocol (MCP) ]
```

---

## 🌟 The 20 Super-Capabilities

| # | Capability | Module | What It Does | Why It Matters |
| :-: | :--- | :--- | :--- | :--- |
| **1** | 🧑‍💻 **Dual-Mode Engine** | `src/cli.py` | Human visual mode or `--agent` / `--json` headless mode. | Works equally well for human engineers and autonomous agents. |
| **2** | 🔌 **Native MCP Server** | `src/mcp_server.py` | Exposes tools over stdio (`git-oops --mcp`). | Instantly attaches to Claude Desktop, Cursor, and Windsurf. |
| **3** | 🛑 **Anti-Thrashing Watchdog** | `src/watchdog.py` | Detects repeated edit-revert oscillations (> 3 times). | Halts runaway agent loops before burning through credits. |
| **4** | 🛡️ **Blast-Radius Firewall** | `src/firewall.py` | Intercepts `rm -rf`, `force-push`, and wildcard deletions. | Prevents rogue agents from wiping out the filesystem. |
| **5** | 🕵️ **Supply-Chain Shield** | `src/firewall.py` | Blocks hallucinated/typosquatted package installs. | Protects against AI package hallucination attacks. |
| **6** | 🚨 **Egress Sniffer Probe** | `src/sentinel.py` | Scans patches for unauthorized phone-home connections. | Blocks trojans and telemetry data exfiltration in patches. |
| **7** | 🔒 **Multi-Agent Mutex** | `src/watchdog.py` | Cooperative file lease locks across multiple agent sub-workers. | Stops concurrent agents from overwriting each other. |
| **8** | 🪞 **Shadow Workspace** | `src/shadow.py` | Dry-runs patches inside an ephemeral clone directory. | Zero-risk experimentation; commits only after full validation. |
| **9** | 👻 **Polyglot Ghost Import Linter** | `src/guardian.py` | 0 ms AST/heuristic check across Python, JS/TS, Go, Rust, Java/Kotlin, C/C++, PHP, Ruby, C#, Swift, Dart, Lua, Shell & exotic scripts. | Blocks patches containing non-existent hallucinated packages in any language. |
| **10**| 🧪 **Regression Guard** | `src/guardian.py` | Runs project tests in sandbox before modifying files. | Prevents agents from breaking existing features. |
| **11**| ⚖️ **Cross-Model Consensus** | `src/consensus.py` | Requires 2 independent models to agree on the root cause. | Eliminates single-model hallucination single-points-of-failure. |
| **12**| ✂️ **Anti-Bloat Complexity** | `src/sentinel.py` | Monitors cyclomatic complexity to prevent code bloat. | Stops agents from writing 8-layer nested spaghetti code. |
| **13**| 📜 **License Taint Shield** | `src/sentinel.py` | Blocks patches containing viral GPL/AGPL copy-paste headers. | Protects commercial projects from open-source license lawsuits. |
| **14**| 📉 **Context Log Squeezer** | `src/squeezer.py` | Compresses 5,000-line stacks to 20 focused lines. | Saves 90% of token context window costs. |
| **15**| 🔒 **Secret Redactor** | `src/squeezer.py` | Automatically masks API keys and tokens (`<REDACTED_SECRET>`). | Prevents credential leakage across external LLMs. |
| **16**| 🧭 **Intent Prefetch Engine** | `src/sentinel.py` | Markov-chain prediction prefetching next-step responses. | Speeds up multi-turn agent tool execution chains to 0 ms. |
| **17**| ✈️ **Flight Recorder** | `src/blackbox.py` | Logs every action, motivation, and takes file snapshots. | Full auditability of what your agent did overnight. |
| **18**| ⏪ **Time-Machine Rewind** | `src/blackbox.py` | `--rewind <step_id>` restores snapshot state. | 1-second recovery if an agent takes a wrong path. |
| **19**| 🧬 **Antibody Immunity DB** | `src/blackbox.py` | Saves verified solutions to a local pathology ledger. | Next time the same error occurs, resolution is instant. |
| **20**| 🔄 **Anti-Bit-Rot Evolution** | `src/updater.py` | Auto-detects runtime shifts and model deprecations. | Code never rots or breaks across future Python releases. |

---

## 🚀 Beginner Quickstart (1-Minute Guide)

### 1. Install Globally:
```bash
git clone https://github.com/Hao610/git-oops.git
cd git-oops
pip install -e .
```

### 2. Connect to Any AI Tool (MCP or Subshell):

#### Option A: For Claude Desktop / Cursor / Windsurf / Antigravity (MCP):
Add this to your MCP configuration:
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

#### Option B: For OpenAI Codex / Qoder / Copilot / Aider / Devin:
Simply tell your agent in prompt or rule:
> *"Always diagnose and apply patches safely via: `git-oops --agent --file <file> --error \"<error>\" --yes`"*
It outputs clean machine-readable JSON without ANSI codes.

### 3. Use it in Terminal:
```bash
# Human mode (roasts you & shows visual diff)
git-oops --file broken.py --error "KeyError: 'user_id'"

# Agent mode (outputs pure JSON)
git-oops --agent --file broken.py --error "KeyError: 'user_id'" --yes
```

---

## 🧪 Comprehensive Test Suite

All 20 test suites run in under 0.25 seconds:

```bash
pytest tests -v
```

```text
============================= 20 passed in 0.20s ==============================
```

---

## 🔒 100% Local & Privacy-First (Zero Telemetry)

We believe developer tools should never spy on you or your AI agents:
- **Zero Telemetry**: No tracking pixels, no user analytics, and zero remote logging.
- **Air-Gapped Safety**: All firewalls, anti-thrashing heuristics, AST parsing, and secret redactors run **100% locally on your machine**.
- **Data Sovereignty**: The blackbox flight recorder, antibody memory DB, and shadow sandboxes live strictly in `~/.git_oops/` in your local home directory.
- **Credential Masking**: High-entropy strings, tokens, and keys are automatically sanitized before reaching any AI model.

---

## 🤝 Documentation & Community

- Check out the [Help & Beginner's Manual](HELP.md) for full MCP step-by-step screenshots and command references.
- Read our [Contributing Guidelines](CONTRIBUTING.md) to set up your environment.
- Review our [Code of Conduct](CODE_OF_CONDUCT.md).
- To report security vulnerabilities privately, please review [SECURITY.md](SECURITY.md).
