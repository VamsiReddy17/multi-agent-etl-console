# Contributing to Multi-Agent ETL Console

Thank you for your interest in contributing to the Multi-Agent ETL Console project! We welcome feedback, bug reports, and code contributions to improve this reference architecture.

---

## 📋 Table of Contents
1. [Code of Conduct](#code-of-conduct)
2. [How to Contribute](#how-to-contribute)
3. [Coding Style & Guidelines](#coding-style--guidelines)
4. [Testing Policies](#testing-policies)
5. [Conventional Commits](#conventional-commits)

---

## 🤝 How to Contribute

### 1. Report Bug / Feature Requests
Please create an issue on GitHub. Include:
- A descriptive title.
- Clear steps to reproduce (for bugs) or user stories (for features).
- Environment details (Docker, macOS/Windows version).

### 2. Submit Pull Requests
1. Fork the repository and create your branch from `main`.
2. Clean and format your code according to our [Style Guidelines](#coding-style--guidelines).
3. Add unit tests for any new helper functions or agent logic.
4. Run the full test suite locally:
   ```bash
   python -m pytest tests/ -v
   ```
5. Push to your fork and submit a PR to `main`.

---

## 🎨 Coding Style & Guidelines

- **Python (PEP 8)**: Use clean PEP 8 styling. Leverage `black` or `flake8` for linting.
- **Node / React**: Use React Functional Components and standard Hooks inside the `monitoring/dashboard/` workspace.
- **SQL Structure**: Keep Data Warehouse tables fully namespaced (e.g. prefixing with the `warehouse.` schema).
- **Agent Contracts**: All new agents **must** adhere to the JSON contract return type:
  ```json
  {
    "status": "success | skipped | error",
    "data": [],
    "rows": 0,
    "duration_ms": 0.0,
    "errors": [],
    "agent": "AgentClassName"
  }
  ```

---

## 🧪 Testing Policies

- All PRs are compiled and tested in GitHub Actions.
- Ensure that you run the mock pipeline integration checks prior to pushing:
  ```bash
  docker exec prod_airflow_webserver pytest /app/tests/ -v
  ```
- Make sure mock anomaly injection limits are kept under 20% in your datasets so that the Quality validation threshold passes.

---

## ✍️ Conventional Commits

We follow the [Conventional Commits specification](https://www.conventionalcommits.org/):
- `feat:` for new capabilities (e.g. `feat: Add BigQuery integration loader`)
- `fix:` for bug fixes (e.g. `fix: Resolve Celery worker connection timeout`)
- `docs:` for documentation updates (e.g. `docs: Update walkthrough steps`)
- `style:` for changes that do not affect code logic (whitespace, formatting)
- `test:` for adding or refactoring test cases
