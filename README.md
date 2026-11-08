<div align="center">

# ⚡ git-oops

### *Turn Any Terminal Crash into a 1-Click Git Patch — Roasted by a Staff Engineer, Protected by an LLM Circuit Breaker.*

<p align="center">
  <img src="cover.jpg" alt="git-oops Hero Banner" width="850" style="border-radius: 10px; margin: 15px 0;" />
</p>

[![CI Suite](https://github.com/Hao610/git-oops/actions/workflows/ci.yml/badge.svg)](https://github.com/Hao610/git-oops/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/Python-3.9%20%7C%203.10%20%7C%203.11%20%7C%203.12-blue?logo=python)](https://www.python.org/)
[![Zero-Dependency](https://img.shields.io/badge/Dependencies-Zero%20Heavy%20C%20Exts-success)]()
[![Spend-Protection](https://img.shields.io/badge/Wallet-Circuit%20Breaker%20Protected-orange)]()
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

</div>

---

## 😤 Why git-oops?

Every developer knows the Friday 11:30 PM ritual:
1. Your script crashes with a 50-line Python or Node stack trace.
2. You copy-paste it into ChatGPT.
3. You get a polite, rambling 6-paragraph essay starting with *"I'd be glad to help! The issue appears to be..."* just to find 2 changed lines of code buried at the bottom.
4. You hook up a local AI agent to fix it, hit a recursive retry loop, and wake up to a **$140 surprise API bill**.

**`git-oops` replaces that entire mess with a single terminal command:**

```bash
git-oops --file broken.py --error "KeyError: 'user_id'"
```

---

## ⚡ What You Get in 1.5 Seconds

```text
⚡ [GIT-OOPS] Analyzing crash & invoking staff-level critic...

💀 THE ROAST:
"Congratulations! You treated an optional dictionary key like it was guaranteed 
by the Geneva Conventions, and now you act shocked when Python slaps you with a KeyError. 
Classic Friday-at-5PM code."

🔍 ROOT CAUSE: Unchecked dictionary subscription without .get() or defensive guard.
💰 COST INCURRED: $0.00012 (Total today: $0.0034)

📝 PROPOSED GIT PATCH:
--- a/broken.py
+++ b/broken.py
@@ -2,2 +2,3 @@
-    user_id = payload["user_id"]
+    user_id = payload.get("user_id")
+    if not user_id:
+        raise ValueError("Missing required user_id in payload")

Apply this patch to 'broken.py' right now? [y/N]: y

✅ Patch applied! Run your script again.
```

---

## 🏗️ Architecture & How It Works

```text
  [Terminal Crash / Traceback]
               │
               ▼
   [Local SHA-256 Cache] ──(Hit?)──> Instant Return ($0.00 Cost, 0ms Latency)
               │ (Miss)
               ▼
   [Daily Circuit Breaker] ──(Spent >= $1.00?)──> Hard Stop! Protects Wallet
               │ (Under budget)
               ▼
   [Staff-Level AI Critic] ───> Generates Brutal Roast + Targeted Git Diff
               │
               ▼
   [Interactive Patcher]   ───> Press [Y] ➔ Surgical In-Place File Update
```

---

## 🌟 Core Pillars

| Feature | What It Does | Why It Matters |
| :--- | :--- | :--- |
| 💀 **Brutal Staff Roast** | Delivers witty, unapologetic technical teardowns of bad habits. | No polite filler. Forces you to learn proper architectural patterns. |
| 📝 **1-Click Surgical Patch** | Generates an exact unified git diff and applies it on `[y]`. | No browser switching. Preserves comments, imports, and indentation. |
| 🛡️ **Budget Circuit Breaker** | Hard-caps daily API spending at a configurable threshold (e.g. $1.00). | Physically impossible to get slapped with runaway $500 agent bills. |
| ⚡ **Deterministic Cache** | Caches responses by code + error SHA-256 hash in `~/.git_oops/`. | Re-running crashes during debugging costs $0.00 and runs offline. |

---

## 🛡️ Circuit Breaker CLI Status

Want to check how much you've spent today?
```bash
python -m src.cli --status
```

Output:
```text
🛡️  [GIT-OOPS CIRCUIT BREAKER STATUS]
Today's Accumulated Spend : $0.00340 USD
Safety Threshold          : $1.00 USD
```

If your usage ever breaches your safety ceiling:
```text
🚨 [CIRCUIT BREAKER TRIGGERED] Daily budget of $1.00 exceeded! (Spent today: $1.0420).
Requests blocked to protect your wallet.
```

---

## 🚀 Quickstart & Installation

### Prerequisites
- Python 3.9+
- A Google Gemini API key (or test offline!)

```bash
# 1. Clone the repository
git clone https://github.com/Hao610/git-oops.git
cd git-oops

# 2. Install dependencies (strictly lightweight: requests & pytest)
pip install -r requirements.txt

# 3. Configure API Key
# Linux / macOS:
export GEMINI_API_KEY="your-gemini-key"
# Windows PowerShell:
$env:GEMINI_API_KEY="your-gemini-key"

# 4. Run git-oops on any crash
python -m src.cli --file broken.py --error "TypeError: unsupported operand type"
```

---

## 🧪 Comprehensive Unit Tests

All 4 test suites verify circuit breaker triggers, SHA-256 deduplication, and patch replacement boundaries:

```bash
pytest tests -v
```

```text
tests/test_oops.py::test_circuit_breaker_blocks_when_exceeded PASSED     [ 25%]
tests/test_oops.py::test_sha256_hashing_consistency PASSED               [ 50%]
tests/test_oops.py::test_patch_application PASSED                        [ 75%]
tests/test_oops.py::test_offline_critic_returns_valid_roast_and_diff PASSED [100%]
============================== 4 passed in 0.22s ==============================
```

---

## 🤝 Community & Contributing

We welcome contributions!
- Read our [Contributing Guidelines](CONTRIBUTING.md) to set up your environment.
- Review our [Code of Conduct](CODE_OF_CONDUCT.md).
- To report security vulnerabilities privately, please review [SECURITY.md](SECURITY.md).

---

## 📄 License

Distributed under the **MIT License**. See [`LICENSE`](LICENSE) for details.
