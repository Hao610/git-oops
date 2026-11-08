<div align="center">

# ⚡ git-oops: The Brutally Honest Terminal Crash Fixer with an LLM Circuit Breaker

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/)
[![Tests Passing](https://img.shields.io/badge/tests-4%2F4%20passed-brightgreen.svg)]()

### *Turn Any Terminal Crash into a 1-Click Git Patch — Roasted by a Staff Engineer, Protected by an API Budget Circuit Breaker.*

</div>

---

## 💡 What is git-oops?

Every developer has been there:
1. Your script crashes with a 40-line Python/Node stack trace.
2. You copy-paste it into ChatGPT or Gemini.
3. You get a polite, rambling 500-word essay just to find 2 changed lines of code.
4. Meanwhile, a recursive script or bad loop burns $50 on your cloud API account.

**git-oops replaces that entire painful cycle with one command:**

```bash
git-oops --file broken.py --error "KeyError: 'user_id'"
```

It immediately gives you:
- 💀 **A Brutally Honest Roast**: Staff-engineer level technical critiques that call out your sloppy anti-patterns.
- 🔍 **Root Cause Diagnosis**: One crisp sentence identifying why it broke.
- 📝 **1-Click Git Patch**: An exact unified diff with an interactive `Apply this patch? [y/N]` prompt.
- 🛡️ **Zero-Dollar Blowout Circuit Breaker**: Hard daily spend limits (default: $1.00) that automatically kill runaway queries before you get slapped with a $500 bill.
- ⚡ **Local SHA256 Deterministic Cache**: Duplicate crash queries are served free and instantly with 0 tokens consumed.

---

## 🚀 Quickstart

```bash
# Clone the repository
git clone https://github.com/Hao610/git-oops.git
cd git-oops

# Install dependencies (only requests & pytest)
pip install -r requirements.txt

# Run the CLI
python -m src.cli --file example.py --error "TypeError: unsupported operand type"
```

## 🛡️ Circuit Breaker in Action

Check your accumulated API spend for today:
```bash
python -m src.cli --status
```
Output:
```text
🛡️  [GIT-OOPS CIRCUIT BREAKER STATUS]
Today's Accumulated Spend : $0.00340 USD
Safety Threshold          : $1.00 USD
```

If your scripts go haywire and breach your set threshold, **git-oops strictly halts**:
```text
🚨 [CIRCUIT BREAKER TRIGGERED] Daily budget of $1.00 exceeded! (Spent today: $1.0420). Requests blocked to protect your wallet.
```

---

## 🧪 Testing

```bash
pytest tests -v
```

## 📄 License
MIT License. Free to use, modify, and integrate into your daily workflow.
