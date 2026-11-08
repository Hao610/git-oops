# Contributing to git-oops

We love your input! We want to make contributing to `git-oops` as easy and transparent as possible, whether it's:

- Reporting a bug
- Discussing the current state of the code
- Submitting a fix
- Proposing new features (e.g. adding new LLM providers, smarter diff algorithms)

---

## 🛠️ Development Setup

1. Fork the repo and create your branch from `main`:
   ```bash
   git checkout -b feature/my-cool-feature
   ```

2. Create a virtual environment and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Or `.\venv\Scripts\activate` on Windows
   pip install -r requirements.txt
   ```

3. Run the automated test suite before opening a PR:
   ```bash
   pytest tests -v
   ```
   *All tests must pass!*

---

## 📜 Pull Request Guidelines

1. **Keep it focused**: One bug fix or one feature per PR.
2. **Include unit tests**: If you add new logic (e.g. a new circuit breaker rule or CLI flag), please add corresponding tests in `tests/`.
3. **Preserve zero-dependency philosophy**: Keep dependencies lean. Avoid heavy external libraries unless strictly necessary.
4. **Pass all CI checks**: GitHub Actions will automatically run the pytest suite on every PR.

---

## 💬 Code of Conduct

Be welcoming, polite, and constructive. (Save the brutality strictly for the AI's code roasting feature! 😄)
