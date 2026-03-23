# Contributing

Thanks for your interest in contributing! This guide will help you get
started.

## Development Setup

1. **Clone the repository**

   ```bash
   git clone https://github.com/Wandersalamander/python-content-tree-generator.git
   cd python-content-tree-generator
   ```

2. **Create a virtual environment**

   ```bash
   python -m venv .venv
   source .venv/bin/activate   # Linux / macOS
   .venv\Scripts\activate      # Windows
   ```

3. **Install in editable mode with dev and test extras**

   ```bash
   pip install -e ".[dev,test]"
   ```

4. **Install the pre-commit hooks**

   ```bash
   pre-commit install
   ```

## Running Tests

```bash
pytest
```

With coverage:

```bash
pytest --cov --cov-report=term-missing
```

## Code Standards

- **Formatting & linting** are handled by [Ruff](https://github.com/astral-sh/ruff).
- **Type checking** is done with [ty](https://github.com/astral-sh/ty).
- **Pre-commit hooks** run automatically on every commit. You can also run
  them manually:

  ```bash
  pre-commit run --all-files
  ```

- All code must include type annotations and pass the type checker.
- Aim for clear, single-responsibility functions with docstrings.

## Submitting Changes

1. Fork the repository and create a feature branch from `main`.
2. Make your changes and add tests where appropriate.
3. Ensure all checks pass (`pre-commit run --all-files && pytest`).
4. Open a pull request with a clear description of the change.

## Reporting Issues

Please use [GitHub Issues](https://github.com/Wandersalamander/python-content-tree-generator/issues)
to report bugs or request features. Include:

- Steps to reproduce (for bugs).
- Expected vs. actual behaviour.
- Python version and OS.
