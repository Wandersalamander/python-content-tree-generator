from __future__ import annotations

import subprocess
import textwrap
from pathlib import Path

import pytest

from python_content_tree_generator.update_contents_md import (
    ContentTree,
    build_content_tree,
    extract_docstring,
    generate_markdown,
    inject_into_file,
)


class TestExtractDocstring:
    def test_single_line_docstring(self, tmp_path: Path) -> None:
        f: Path = tmp_path / "mod.py"
        f.write_text('"""Hello world."""\n', encoding="utf-8")
        assert extract_docstring(f) == "Hello world."

    def test_multiline_docstring_returns_first_line(
        self,
        tmp_path: Path,
    ) -> None:
        f: Path = tmp_path / "mod.py"
        f.write_text(
            textwrap.dedent('''\
                """First line.

                More details here.
                """
            '''),
            encoding="utf-8",
        )
        assert extract_docstring(f) == "First line."

    def test_no_docstring(self, tmp_path: Path) -> None:
        f: Path = tmp_path / "mod.py"
        f.write_text("x = 1\n", encoding="utf-8")
        assert extract_docstring(f) == ""

    def test_empty_file(self, tmp_path: Path) -> None:
        f: Path = tmp_path / "mod.py"
        f.write_text("", encoding="utf-8")
        assert extract_docstring(f) == ""


def _git_init(path: Path) -> None:
    """Initialise a git repo and track all files under *path*."""
    subprocess.run(["git", "init"], cwd=path, capture_output=True, check=True)
    subprocess.run(
        ["git", "add", "."],
        cwd=path,
        capture_output=True,
        check=True,
    )


class TestBuildContentTree:
    def _make_project(self, tmp_path: Path) -> None:
        (tmp_path / "main.py").write_text(
            '"""Main module."""\n',
            encoding="utf-8",
        )
        (tmp_path / "utils.py").write_text(
            '"""Utilities."""\n',
            encoding="utf-8",
        )
        sub: Path = tmp_path / "sub"
        sub.mkdir()
        (sub / "helper.py").write_text('"""Helper."""\n', encoding="utf-8")
        (sub / "not_python.txt").write_text("ignore me", encoding="utf-8")
        _git_init(tmp_path)

    def test_collects_all_files(self, tmp_path: Path) -> None:
        self._make_project(tmp_path)
        tree: ContentTree = build_content_tree(tmp_path)
        assert "main.py" in tree
        assert "utils.py" in tree
        assert "sub" in tree
        assert "helper.py" in tree["sub"]
        assert "not_python.txt" in tree["sub"]

    def test_ignore_files(self, tmp_path: Path) -> None:
        self._make_project(tmp_path)
        tree: ContentTree = build_content_tree(
            tmp_path,
            ignore_files=("utils.py",),
        )
        assert "utils.py" not in tree
        assert "main.py" in tree

    def test_empty_directory(self, tmp_path: Path) -> None:
        _git_init(tmp_path)
        assert build_content_tree(tmp_path) == {}

    def test_no_docstrings_by_default(self, tmp_path: Path) -> None:
        self._make_project(tmp_path)
        tree: ContentTree = build_content_tree(tmp_path)
        assert tree["main.py"] is None

    def test_docstrings_when_enabled(self, tmp_path: Path) -> None:
        self._make_project(tmp_path)
        tree: ContentTree = build_content_tree(tmp_path, docstrings=True)
        assert tree["main.py"] == "Main module."
        assert tree["sub"]["helper.py"] == "Helper."


class TestGenerateMarkdown:
    def test_tree_format(self) -> None:
        tree: ContentTree = {"sub": {"hello.py": None}, "README.md": None}
        md: str = generate_markdown(tree, "myproject")
        assert md.startswith("\n```\n")
        assert md.endswith("\n```\n")
        assert "myproject/" in md
        assert "├──" in md or "└──" in md

    def test_directories_before_files(self) -> None:
        tree: ContentTree = {"zebra.py": None, "alpha": {"a.py": None}}
        md: str = generate_markdown(tree, "proj")
        lines: list[str] = md.split("\n")
        dir_line: str = next(l1 for l1 in lines if "alpha/" in l1)
        file_line: str = next(l2 for l2 in lines if "zebra.py" in l2)
        assert lines.index(dir_line) < lines.index(file_line)

    def test_docstring_suffix(self) -> None:
        tree: ContentTree = {"app.py": "My app"}
        md: str = generate_markdown(tree, "proj")
        assert "app.py  # My app" in md

    def test_no_docstring_no_suffix(self) -> None:
        tree: ContentTree = {"app.py": None}
        md: str = generate_markdown(tree, "proj")
        assert "app.py" in md
        assert "#" not in md

    def test_empty_tree(self) -> None:
        md: str = generate_markdown({}, "proj")
        lines: list[str] = md.strip().split("\n")
        assert lines[0] == "```"
        assert lines[1] == "proj/"
        assert lines[2] == "│"
        assert lines[3] == "```"

    def test_nested_structure(self) -> None:
        tree: ContentTree = {
            "src": {"__init__.py": None, "main.py": None},
            "unittest": {"test_main.py": None},
            "README.md": None,
        }
        md: str = generate_markdown(tree, "myproject")
        assert "myproject/" in md
        assert "src/" in md
        assert "unittest/" in md
        assert "__init__.py" not in md
        assert "README.md" in md

    def test_init_docstring_promoted_to_directory(self) -> None:
        tree: ContentTree = {
            "components": {
                "__init__.py": "Component descriptors.",
                "element.py": "Element components.",
            },
        }
        md: str = generate_markdown(tree, "proj")
        assert "components/  # Component descriptors." in md
        assert "__init__.py" not in md
        assert "element.py  # Element components." in md

    def test_init_without_docstring_still_hidden(self) -> None:
        tree: ContentTree = {
            "pkg": {"__init__.py": None, "mod.py": None},
        }
        md: str = generate_markdown(tree, "proj")
        assert "__init__.py" not in md
        assert "pkg/" in md
        assert "mod.py" in md

    def test_init_empty_docstring_still_hidden(self) -> None:
        tree: ContentTree = {
            "pkg": {"__init__.py": "", "mod.py": None},
        }
        md: str = generate_markdown(tree, "proj")
        assert "__init__.py" not in md
        assert "pkg/" in md
        assert "#" not in md.split("pkg/")[1].split("\n")[0]


class TestInjectIntoFile:
    def test_injects_between_markers(self, tmp_path: Path) -> None:
        f: Path = tmp_path / "README.md"
        f.write_text(
            "# My Project\n\n<!-- content-tree -->\nold stuff\n<!-- /content-tree -->\n\nFooter\n",
            encoding="utf-8",
        )
        assert inject_into_file(f, "tree content\n") is True
        text: str = f.read_text(encoding="utf-8")
        assert "old stuff" not in text
        assert "tree content\n" in text
        assert text.startswith("# My Project\n")
        assert text.endswith("Footer\n")

    def test_no_change_returns_false(self, tmp_path: Path) -> None:
        f: Path = tmp_path / "README.md"
        f.write_text(
            "# Title\n<!-- content-tree -->\nhello\n<!-- /content-tree -->\n",
            encoding="utf-8",
        )
        assert inject_into_file(f, "hello\n") is False

    def test_missing_markers_raises(self, tmp_path: Path) -> None:
        f: Path = tmp_path / "README.md"
        f.write_text("# No markers here\n", encoding="utf-8")
        with pytest.raises(ValueError, match="missing marker"):
            inject_into_file(f, "tree\n")
        # File must remain untouched
        assert f.read_text(encoding="utf-8") == "# No markers here\n"

    def test_file_not_found_raises(self, tmp_path: Path) -> None:
        missing: Path = tmp_path / "does_not_exist.md"
        with pytest.raises(FileNotFoundError, match="file not found"):
            inject_into_file(missing, "tree\n")

    def test_preserves_surrounding_content(self, tmp_path: Path) -> None:
        f: Path = tmp_path / "README.md"
        f.write_text(
            "before\n<!-- content-tree -->\nold\n<!-- /content-tree -->\nafter\n",
            encoding="utf-8",
        )
        inject_into_file(f, "new\n")
        text: str = f.read_text(encoding="utf-8")
        assert text.startswith("before\n")
        assert text.endswith("after\n")
