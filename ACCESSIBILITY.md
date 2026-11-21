# Accessibility Statement (A11y) — git-oops v1.1.0

The `git-oops` project is dedicated to ensuring that both our terminal CLI and our real-time Obsidian Glassmorphism Web HUD (`http://localhost:8443`) are fully accessible, inclusive, and ergonomic for all developers, operators, and neurodivergent engineers.

---

## 🌟 Core Accessibility Principles

1. **Terminal-First & Screen Reader Friendly**:
   - Every CLI status, error message, and diff output uses clean semantic text streams (`stdout` and `stderr`) that screen readers (NVDA, JAWS, VoiceOver) can parse without clutter.
   - Text output avoids reliance on raw ANSI color sequences alone: critical warnings always include explicit text prefixes such as `[CRITICAL]`, `[BLOCKED]`, `[WARNING]`, or `[SUCCESS]`.

2. **Web HUD (Obsidian Glassmorphism) Standards (WCAG 2.1 AA Target)**:
   - **Contrast Ratios**: Body text, status indicators, and diff tokens adhere strictly to minimum contrast ratios (at least 4.5:1 for regular text and 3:1 for large text / graphical UI components).
   - **Keyboard Navigability**: All interactive controls, audit logs, filter dropdowns, and reflog recovery buttons are accessible via keyboard (`Tab`, `Shift+Tab`, `Enter`, `Escape`).
   - **Focus States**: High-visibility focus rings and outlines are preserved across all buttons and clickable elements.
   - **No Flashing Content**: Transitions and pulse animations respect system accessibility preferences (`prefers-reduced-motion: reduce`).

3. **Color-Blind Ergonomics**:
   - Diff views, circuit breaker states, and severity badges never convey meaning through color alone.
   - Red/Green status badges are accompanied by distinct iconography (`✕ BLOCKED`, `✓ ALLOWED`, `⚡ ACTIVE`, `⚠ CAUTION`).

4. **Cognitive & Neurodivergent Accessibility**:
   - Clear, predictable interface layouts.
   - Distraction-free modes and readable typography with generous line heights.
   - Zero aggressive auto-refresh jumps or disruptive popups: user scroll position in the Blackbox audit trail is strictly maintained.

---

## 🛠️ Supported Standards & Assistive Technologies

- **WCAG 2.1 Guidelines**: Level AA compliance target.
- **Terminal Standards**: Standard POSIX/Windows console accessibility conformance.
- **Assistive Software**:
  - VoiceOver (macOS / iOS)
  - NVDA & JAWS (Windows)
  - Orca (Linux)

---

## 💬 Feedback & Reporting Accessibility Barriers

We welcome community feedback to improve accessibility across all `git-oops` tools. If you encounter any accessibility barrier or have suggestions:

- **GitHub Issues**: Open an issue labeled `accessibility` on [GitHub Issues](https://github.com/Hao610/git-oops/issues).
- **Security & Privacy Advisories**: For sensitive disclosures, report via [GitHub Security Advisories](https://github.com/Hao610/git-oops/security/advisories).

We are committed to resolving accessibility issues promptly in accordance with our v1.1.x release lifecycle.
