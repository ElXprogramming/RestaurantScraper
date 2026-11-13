# Contributing to RestaurantScraper

Thank you for your interest in contributing to **RestaurantScraper**! We welcome bug reports, parser improvements, documentation updates, and feature proposals.

---

## 🛠️ Development Setup

1. **Fork and Clone the Repository**:
   ```bash
   git clone https://github.com/<your-username>/RestaurantScraper.git
   cd RestaurantScraper
   ```

2. **Create and Activate a Virtual Environment**:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install Dependencies in Editable Mode**:
   ```bash
   pip install -r requirements.txt
   pip install -e ".[dev]"
   ```

4. **Verify Installation**:
   ```bash
   restaurantscraper --help
   pytest tests -v
   ```

---

## 🧪 Testing Guidelines

- Add or update offline unit tests in `tests/` for extraction logic, database operations, sanitization, CLI commands, or server handlers.
- Run the full suite before opening a pull request:
  ```bash
  pytest tests -v
  ```

---

## 💡 Submitting Issues & Pull Requests

1. **Bug Reports**: Open an issue with your OS, Python version, reproduction steps, and error traceback.
2. **Feature Requests**: Describe the target restaurant platform, export format, or CLI/GUI enhancement.
3. **Pull Requests**:
   - Branch from `main`: `git checkout -b feat/my-feature`
   - Keep commits focused and descriptive.
   - Ensure `pytest tests -v` passes completely.

---

## 📜 Code of Conduct

Please review and adhere to our [Code of Conduct](CODE_OF_CONDUCT.md) in all community interactions.
