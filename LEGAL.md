# Legal Information & Terms of Use

Last Updated: November 2026

Welcome to **git-oops**. Please read this document carefully before utilizing the software, its command-line interfaces, background hooks, Model Context Protocol (MCP) servers, or autonomous safety harnesses.

---

## 1. Open Source License & Terms

`git-oops` is licensed under the permissive **MIT License**.

Copyright (c) 2026 Hao and contributors.

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

---

## 2. Disclaimer of Warranties and Limitation of Liability

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, AND NONINFRINGEMENT.

IN NO EVENT SHALL THE AUTHORS, COPYRIGHT HOLDERS, OR CONTRIBUTORS BE LIABLE FOR ANY CLAIM, DAMAGES, OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT, OR OTHERWISE, ARISING FROM, OUT OF, OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

This includes, without limitation:
- Any accidental loss of source code or data resulting from Git commands, branch operations, or reflog autopsies.
- Any bugs, security vulnerabilities, or regressions introduced by AI-generated or automated patches.
- Any disruptions caused by process throttling, E-Core scheduling, or command firewall interceptions.

---

## 3. Autonomous AI Agents & Generative Code Notice

`git-oops` provides runtime observation, heuristic firewalls, and guardrails for autonomous coding agents (including but not limited to agents powered by OpenAI, Anthropic, Google, DeepSeek, or local Ollama/vLLM models).

1. **Human Oversight**: Users acknowledge that generative AI models are probabilistic and may hallucinate code or commands. Users and operators retain ultimate responsibility for auditing and reviewing all patches before committing or deploying code to production environments.
2. **Safe Mode Enforcement**: By default, `git-oops` prompts human operators before applying changes. When running in headless agent mode (`--agent`, `--yes`), the operator explicitly assumes responsibility for automated actions executed by their autonomous workflows.

---

## 4. Privacy, Data Sovereignty & Zero-Telemetry Guarantee

We believe developer tools must respect privacy:
- **No Remote Telemetry**: `git-oops` does NOT transmit user analytics, hardware fingerprints, file contents, or usage telemetry to any centralized or proprietary servers.
- **Local State Storage**: All audit trails, blackbox flight records, local cache databases, and crash snapshots are stored strictly on the local machine under `~/.git_oops/`.
- **Secret Redaction**: Automated redactors actively sanitize sensitive API tokens (such as AWS keys, OpenAI tokens, and GitHub personal access tokens) prior to log processing.

---

## 5. Third-Party Trademarks & Attributions

- **Git** is a registered trademark of the Software Freedom Conservancy.
- **Python** is a registered trademark of the Python Software Foundation.
- **GitHub** is a registered trademark of GitHub, Inc.
- **OpenAI**, **Anthropic**, **Google**, **Claude**, **Cursor**, **Windsurf**, and **PyPI** are trademarks or registered trademarks of their respective owners.
- **Kaggle** is a trademark of Kaggle Inc. / Google LLC. This project is completely independent and has zero affiliation, endorsement, sponsorship, or association with Kaggle or Google LLC.
- Reference to any third-party products, services, or trademarks is solely for nominative identification, compatibility purposes, and interoperability reference, and does not imply endorsement or affiliation.
