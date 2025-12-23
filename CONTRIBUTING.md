# Contributing to AIQuorum

First off, thanks for taking the time to contribute! 🎉

The following is a set of guidelines for contributing to AIQuorum. These are mostly guidelines, not rules. Use your best judgment, and feel free to propose changes to this document in a pull request.

## 🛠️ Development Setup

1.  **Fork the repo** and clone it locally.
2.  **Create a virtual environment**:
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # On Windows: .venv\Scripts\activate
    ```
3.  **Install dependencies**:
    ```bash
    pip install -e .[dev]
    ```
4.  **Run Tests**:
    ```bash
    pytest
    ```

## 🏗️ Project Structure

- `src/aiquorum`: Main source code.
- `tests`: Unit and integration tests.
- `examples`: Demo scripts and notebooks.

## 📝 Code Style

- We follow **PEP 8** guidelines.
- Please use type hints in all new functions.
- Run `mypy` if possible to check types.

## 🚀 Submitting a Pull Request

1.  Create a new branch: `git checkout -b feature/my-new-feature`
2.  Commit your changes: `git commit -am 'Add some feature'`
3.  Push to the branch: `git push origin feature/my-new-feature`
4.  Submit a pull request!

## 🐛 Reporting Bugs

Bugs are tracked as GitHub issues. When filing an issue, please include:
- A clear title and description.
- A minimal reproduction code snippet.
- Your Python version and OS.

Thank you for helping improve AIQuorum!
