# Python Content Tree Generator

[![CI](https://github.com/Wandersalamander/python-content-tree-generator/actions/workflows/ci.yml/badge.svg)](https://github.com/Wandersalamander/python-content-tree-generator/actions/workflows/ci.yml)
[![Lint](https://github.com/Wandersalamander/python-content-tree-generator/actions/workflows/lint.yml/badge.svg)](https://github.com/Wandersalamander/python-content-tree-generator/actions/workflows/lint.yml)
[![codecov](https://codecov.io/gh/Wandersalamander/python-content-tree-generator/graph/badge.svg)](https://codecov.io/gh/Wandersalamander/python-content-tree-generator)
[![Python 3.10+](https://img.shields.io/python/required-version-toml?tomlFilePath=https%3A%2F%2Fraw.githubusercontent.com%2FWandersalamander%2Fpython-content-tree-generator%2Fmain%2Fpyproject.toml)](https://github.com/Wandersalamander/python-content-tree-generator)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)](https://pre-commit.com/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![License](https://img.shields.io/github/license/Wandersalamander/python-content-tree-generator)](https://github.com/Wandersalamander/python-content-tree-generator/blob/main/LICENSE)

A [pre-commit](https://pre-commit.com/) hook that automatically generates and
maintains a `README.md` with an ASCII tree overview of your Python project
structure. Optionally includes first-line module docstrings as inline
comments and promotes `__init__.py` docstrings to the package (folder) level.

## Example Output

```
MyProject/
│
├── components/  # Component descriptor definitions.
│   │
│   ├── element.py  # Element components.
│   ├── particle.py  # Particle components.
│   └── record.py  # Record components.
│
├── tests/
│   │
│   └── test_main.py
│
├── main.py  # Application entry point.
├── setup.py
└── README.md
```

## Installation

Add the hook to your `.pre-commit-config.yaml`:

```yaml
- repo: https://github.com/Wandersalamander/python-content-tree-generator/
  rev: v0.0.7
  hooks:
    - id: content-tree-generator
      args: [
        "--root-dir",
        "./YourPythonProject",
        "--inject",
        "README.md",
        "--docstrings",
      ]
```

## Options

| Flag | Description |
|---|---|
| `--root-dir DIR` | **(required)** Root directory of the Python project to scan. |
| `--output FILE` | Standalone output file (default: `content_tree.md`). |
| `--docstrings` | Include first-line module docstrings as `# …` comments. `__init__.py` docstrings are shown on the folder line instead of as a separate entry. |
| `--ignore FILE …` | File names to exclude from the tree. |
| `--inject FILE …` | Files to inject the tree into (between marker comments). |

## Auto-Injecting into Your README

Instead of maintaining a separate file you can embed the tree directly in any
Markdown file. Add the following marker pair where you want the tree to appear:

```markdown
<!-- content-tree -->
<!-- /content-tree -->
```

Then pass `--inject README.md` (or any other path). On every run the hook
replaces everything between the markers with the latest tree wrapped in a
fenced code block. Content outside the markers is left untouched.

## Contributing

Contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for
development setup, coding standards, and how to submit changes.

## License

Distributed under the [GPL-2.0](LICENSE) license.
