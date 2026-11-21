# Security Policy

## Supported Versions

We release patches and security updates for the current active release line.

| Version | Supported          |
| ------- | ------------------ |
| 1.1.x   | :white_check_mark: |
| 1.0.x   | :white_check_mark: |
| 0.2.x   | :white_check_mark: |
| 0.1.x   | :white_check_mark: |

---

## 🔒 100% Local & Sovereignty Guarantee (The 8 Pillars of Defense)

`git-oops` is engineered from the ground up to guarantee absolute developer and enterprise sovereignty:
- **Zero Telemetry**: No analytics, no phone-home pings, no external usage tracking.
- **Air-Gapped Execution**: All firewalls, AST lexical decomposition, anti-slop complexity checks, secret redactors, and kill switches run 100% locally.
- **L1-L8 Full-Spectrum Protection**:
  - **L1 (Safety Guard)**: Irreversible destructive command prevention (`git reset --hard`, destructive aliases).
  - **L2 (Execution Firewall)**: Shlex AST execution gating against shell hijacking (`curl | bash`).
  - **L3 (Audit & Pre-Flight)**: Air-gapped Blackbox flight recorder and Reflog Autopsy lifeboats.
  - **L4 (Anti-Slop Engine)**: Pre-commit cyclomatic complexity enforcement and test-deletion fraud prevention.
  - **L5 (Supply Chain Armor)**: Phantom dependency hallucination interception and high-entropy secret masking.
  - **L6 (Cognitive Alignment)**: Semantic intent drift gating and multi-agent collusion defense.
  - **L7 (Sovereignty & Air-Gap)**: Out-of-bounds network containment and hardware kill switches.
  - **L8 (The Human Operator)**: Panic protection, anti-gaslighting warnings, and operator sanity confirmation.
- **Local Storage Isolation**: Flight recorder logs, snapshots, and antibody databases reside strictly under `~/.git_oops/` on your local workstation.

---

## Reporting a Vulnerability

The `git-oops` team takes security, agent sandbox boundaries, and developer privacy seriously:
1. **API Key & Secret Exposure**: Ensuring secrets are never logged, cached in plain text, or emitted across session boundaries.
2. **Local Arbitrary Code Execution**: Ensuring patches applied by autonomous agents cannot execute malicious unverified payloads without explicit confirmation.
3. **Execution Firewall Integrity**: Ensuring syntax decomposition cannot be subverted by obscure subshell chaining or multi-stage eval expressions.

If you discover a security vulnerability within `git-oops`, please **do not open a public GitHub issue**. Instead, report it privately:

1. Open a **Private Security Advisory** on GitHub via the **Security** tab of this repository.
2. Provide a detailed summary of the vulnerability, including reproducible steps or proof-of-concept shell snippets.

### What to Expect:
- **Initial Response**: Within 24-48 hours acknowledging receipt of your report.
- **Triage & Patch**: A fix will be developed in a private branch and released promptly under `1.1.x`.
- **Credit**: You will be credited in the security advisory and release notes (unless you prefer anonymity).
