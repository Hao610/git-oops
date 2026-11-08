# Security Policy

## Supported Versions

We release patches and security updates for the current major branch.

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

---

## Reporting a Vulnerability

The `git-oops` team takes security and user privacy seriously, especially regarding:
1. **API Key Exposure**: Ensuring keys are never logged, cached in plain text, or leaked across sessions.
2. **Local Arbitrary Code Execution**: Ensuring patches applied to local files cannot execute malicious payloads without explicit user confirmation.
3. **Circuit Breaker Integrity**: Ensuring budget limits cannot be bypassed by recursive triggers.

If you discover a security vulnerability within `git-oops`, please **do not open a public GitHub issue**. Instead, please report it privately:

1. Open a **Private Security Advisory** on GitHub via the **Security** tab of this repository.
2. Provide a detailed summary of the vulnerability, including reproducible steps or proof-of-concept code.

### What to Expect:
- **Initial Response**: Within 48 hours acknowledging receipt of your report.
- **Triage & Patch**: A fix will be developed in a private branch and released promptly.
- **Credit**: You will be credited in the security advisory and release notes (unless you prefer anonymity).
