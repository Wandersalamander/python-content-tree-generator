from __future__ import annotations

import ast
import subprocess
from pathlib import Path
from typing import Union

PIPE = "│"
ELBOW = "└──"
TEE = "├──"
PIPE_PREFIX = "│   "
SPACE_PREFIX = "    "

DEFAULT_IGNORE_DIRS: frozenset[str] = frozenset(
    {
        ".git",
        ".hg",
        ".svn",
        "__pycache__",
        ".mypy_cache",
        ".ruff_cache",
        ".pytest_cache",
        "node_modules",
        ".venv",
        "venv",
        ".env",
        "env",
        ".idea",
        ".vscode",
        ".tox",
        ".nox",
        "build",
        "dist",
        "*.egg-info",
    },
)

# A content tree node: directories map to nested dicts, files map to
# their docstring (str) or None when docstrings are disabled.
ContentTree = dict[str, Union["ContentTree", str, None]]


def _should_ignore_dir(
    name: str,
    ignore_dirs: frozenset[str],
) -> bool:
    """Check if a directory name matches any ignore pattern."""
    if name in ignore_dirs:
        return True
    # Support *.egg-info style suffix patterns
    for pattern in ignore_dirs:
        if pattern.startswith("*") and name.endswith(pattern[1:]):
            return True
    return False


def extract_docstring(file_path: str | Path) -> str:
    """Extract the first-line module docstring of a Python file."""
    with open(file_path, encoding="utf-8") as f:
        source = f.read()
    tree = ast.parse(source)
    docstring = ast.get_docstring(tree)
    if docstring is None:
        return ""
    if "\n" in docstring:
        return docstring[: docstring.index("\n")]
    return docstring


def _git_tracked_files(root_dir: Path) -> list[str]:
    """Return git-tracked file paths relative to *root_dir*."""
    result = subprocess.run(
        ["git", "ls-files"],
        cwd=root_dir,
        capture_output=True,
        text=True,
        check=True,
    )
    return [line for line in result.stdout.splitlines() if line]


def build_content_tree(
    root_dir: str | Path,
    *,
    ignore_files: tuple[str, ...] = (),
    ignore_dirs: frozenset[str] = DEFAULT_IGNORE_DIRS,
    docstrings: bool = False,
) -> ContentTree:
    """Recursively collect git-tracked files into a nested dict.

    Returns a dict where keys are entry names and values are either:
    - nested dicts (directories)
    - docstring str or None (files)
    """
    root = Path(root_dir).resolve()
    tracked = _git_tracked_files(root)

    tree: ContentTree = {}
    for rel_path_str in sorted(tracked):
        rel_path = Path(rel_path_str)
        parts = rel_path.parts

        # Skip files in ignored directories
        if any(_should_ignore_dir(p, ignore_dirs) for p in parts[:-1]):
            continue

        filename = parts[-1]
        if filename in ignore_files:
            continue

        # Navigate to the correct nested dict
        node: ContentTree = tree
        for part in parts[:-1]:
            node = node.setdefault(part, {})

        full_path = root / rel_path
        doc: str | None = None
        if docstrings and filename.endswith(".py"):
            doc = extract_docstring(full_path)
        node[filename] = doc
    return tree


def _format_tree_lines(
    tree: ContentTree,
    prefix: str = "",
) -> list[str]:
    """Recursively format a nested dict into tree lines.

    When a directory contains an ``__init__.py``, its docstring is
    promoted to the directory line and the file itself is omitted from
    the listing.
    """
    lines: list[str] = []
    entries = list(tree.items())
    dirs = [(k, v) for k, v in entries if isinstance(v, dict)]
    files = [
        (k, v)
        for k, v in entries
        if not isinstance(v, dict) and k != "__init__.py"
    ]

    # Directories first, then files
    ordered: list[tuple[str, ContentTree | str | None]] = dirs + files
    for i, (name, value) in enumerate(ordered):
        is_last: bool = i == len(ordered) - 1
        connector: str = ELBOW if is_last else TEE
        if isinstance(value, dict):
            # Promote __init__.py docstring to the directory line
            init_doc: str | None = value.get("__init__.py")
            dir_suffix: str = (
                f"  # {init_doc}"
                if isinstance(init_doc, str) and init_doc
                else ""
            )
            lines.append(f"{prefix}{connector} {name}/{dir_suffix}")
            extension: str = SPACE_PREFIX if is_last else PIPE_PREFIX
            lines.append(f"{prefix}{extension}{PIPE}")
            sub_lines = _format_tree_lines(value, prefix + extension)
            lines.extend(sub_lines)
            # Add blank pipe line after directory block (unless last entry)
            if not is_last:
                lines.append(f"{prefix}{PIPE}")
        else:
            doc_suffix: str = f"  # {value}" if value else ""
            lines.append(f"{prefix}{connector} {name}{doc_suffix}")
    return lines


def generate_markdown(tree: ContentTree, root_name: str) -> str:
    """Generate a tree-style content listing."""
    lines: list[str] = [f"{root_name}/", PIPE]
    lines.extend(_format_tree_lines(tree))
    return "\n```\n" + "\n".join(lines) + "\n```\n"


BEGIN_MARKER: str = "<!-- content-tree -->"
END_MARKER: str = "<!-- /content-tree -->"


def inject_into_file(file_path: Path, content: str) -> bool:
    """Replace the section between markers in a file with new content.

    Returns True if the file was changed, False if already up to date.

    Raises
    ------
    FileNotFoundError
        If *file_path* does not exist.
    ValueError
        If the file exists but does not contain the required marker
        pair (``<!-- content-tree -->`` … ``<!-- /content-tree -->``).
    """
    if not file_path.exists():
        raise FileNotFoundError(
            f"Cannot inject into '{file_path}': file not found.",
        )

    text: str = file_path.read_text(encoding="utf-8")
    begin_idx: int = text.find(BEGIN_MARKER)
    end_idx: int = text.find(END_MARKER)

    if begin_idx == -1 or end_idx == -1:
        missing: list[str] = []
        if begin_idx == -1:
            missing.append(BEGIN_MARKER)
        if end_idx == -1:
            missing.append(END_MARKER)
        raise ValueError(
            f"Cannot inject into '{file_path}': "
            f"missing marker(s) {', '.join(missing)}. "
            f"Add the markers to the file where you want the "
            f"tree to appear.",
        )

    replacement: str = f"{BEGIN_MARKER}\n{content}{END_MARKER}"
    new_text: str = (
        text[:begin_idx] + replacement + text[end_idx + len(END_MARKER) :]
    )
    if new_text == text:
        return False
    file_path.write_text(new_text, encoding="utf-8")
    return True
