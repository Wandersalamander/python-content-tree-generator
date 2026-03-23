from __future__ import annotations

import subprocess
from pathlib import Path

from python_content_tree_generator.hook import main


def _git_init(path: Path) -> None:
    """Initialise a git repo and track all files under *path*."""
    subprocess.run(["git", "init"], cwd=path, capture_output=True, check=True)
    subprocess.run(
        ["git", "add", "."],
        cwd=path,
        capture_output=True,
        check=True,
    )


def _git(path: Path, *args: str) -> subprocess.CompletedProcess[str]:
    """Run a git command in *path* and return the result."""
    return subprocess.run(
        ["git", *args],
        cwd=path,
        capture_output=True,
        text=True,
        check=True,
    )


class TestHookMain:
    def _make_project(self, tmp_path: Path) -> None:
        (tmp_path / "app.py").write_text(
            '"""Application entry."""\n',
            encoding="utf-8",
        )
        (tmp_path / "lib.py").write_text(
            '"""Library code."""\n',
            encoding="utf-8",
        )
        _git_init(tmp_path)

    def test_creates_output_file(self, tmp_path: Path) -> None:
        self._make_project(tmp_path)
        output: Path = tmp_path / "content_tree.md"
        rc: int = main(["--root-dir", str(tmp_path), "--output", str(output)])
        assert rc == 1
        assert output.exists()
        text: str = output.read_text(encoding="utf-8")
        assert "app.py" in text
        assert "lib.py" in text

    def test_no_change_returns_zero(self, tmp_path: Path) -> None:
        project: Path = tmp_path / "project"
        project.mkdir()
        (project / "app.py").write_text('"""App."""\n', encoding="utf-8")
        _git_init(project)
        output: Path = tmp_path / "content_tree.md"
        main(["--root-dir", str(project), "--output", str(output)])
        rc: int = main(["--root-dir", str(project), "--output", str(output)])
        assert rc == 0

    def test_detects_stale_file(self, tmp_path: Path) -> None:
        self._make_project(tmp_path)
        output: Path = tmp_path / "content_tree.md"
        output.write_text("stale content", encoding="utf-8")
        rc: int = main(["--root-dir", str(tmp_path), "--output", str(output)])
        assert rc == 1

    def test_ignore_flag(self, tmp_path: Path) -> None:
        self._make_project(tmp_path)
        output: Path = tmp_path / "content_tree.md"
        main(
            [
                "--root-dir",
                str(tmp_path),
                "--output",
                str(output),
                "--ignore",
                "lib.py",
            ],
        )
        text: str = output.read_text(encoding="utf-8")
        assert "lib.py" not in text
        assert "app.py" in text

    def test_docstrings_flag(self, tmp_path: Path) -> None:
        self._make_project(tmp_path)
        output: Path = tmp_path / "content_tree.md"
        main(
            [
                "--root-dir",
                str(tmp_path),
                "--output",
                str(output),
                "--docstrings",
            ],
        )
        text: str = output.read_text(encoding="utf-8")
        assert "# Application entry." in text

    def test_tree_format(self, tmp_path: Path) -> None:
        self._make_project(tmp_path)
        output: Path = tmp_path / "content_tree.md"
        main(["--root-dir", str(tmp_path), "--output", str(output)])
        text: str = output.read_text(encoding="utf-8")
        assert text.startswith("\n```\n")
        assert f"{tmp_path.name}/" in text
        assert "├──" in text or "└──" in text

    def test_inject_into_readme(self, tmp_path: Path) -> None:
        project: Path = tmp_path / "project"
        project.mkdir()
        (project / "app.py").write_text('"""App."""\n', encoding="utf-8")
        _git_init(project)
        readme: Path = tmp_path / "README.md"
        readme.write_text(
            "# Title\n\n<!-- content-tree -->\n<!-- /content-tree -->\n\nFooter\n",
            encoding="utf-8",
        )
        output: Path = tmp_path / "content_tree.md"
        rc: int = main(
            [
                "--root-dir",
                str(project),
                "--output",
                str(output),
                "--inject",
                str(readme),
            ],
        )
        assert rc == 1
        text: str = readme.read_text(encoding="utf-8")
        assert "app.py" in text
        assert text.startswith("# Title\n")
        assert text.endswith("Footer\n")

    def test_inject_no_change_returns_zero(self, tmp_path: Path) -> None:
        project: Path = tmp_path / "project"
        project.mkdir()
        (project / "app.py").write_text('"""App."""\n', encoding="utf-8")
        _git_init(project)
        readme: Path = tmp_path / "README.md"
        readme.write_text(
            "# Title\n<!-- content-tree -->\n<!-- /content-tree -->\n",
            encoding="utf-8",
        )
        output: Path = tmp_path / "content_tree.md"
        main(
            [
                "--root-dir",
                str(project),
                "--output",
                str(output),
                "--inject",
                str(readme),
            ],
        )
        rc: int = main(
            [
                "--root-dir",
                str(project),
                "--output",
                str(output),
                "--inject",
                str(readme),
            ],
        )
        assert rc == 0

    def test_inject_missing_markers_prints_error(
        self,
        tmp_path: Path,
        capsys: object,
    ) -> None:
        project: Path = tmp_path / "project"
        project.mkdir()
        (project / "app.py").write_text('"""App."""\n', encoding="utf-8")
        _git_init(project)
        readme: Path = tmp_path / "README.md"
        readme.write_text("# No markers\n", encoding="utf-8")
        output: Path = tmp_path / "content_tree.md"
        rc: int = main(
            [
                "--root-dir",
                str(project),
                "--output",
                str(output),
                "--inject",
                str(readme),
            ],
        )
        assert rc == 1
        captured = capsys.readouterr()  # type: ignore[union-attr]
        assert "missing marker" in captured.out

    def test_inject_file_not_found_prints_error(
        self,
        tmp_path: Path,
        capsys: object,
    ) -> None:
        project: Path = tmp_path / "project"
        project.mkdir()
        (project / "app.py").write_text('"""App."""\n', encoding="utf-8")
        _git_init(project)
        missing: Path = tmp_path / "nope.md"
        output: Path = tmp_path / "content_tree.md"
        rc: int = main(
            [
                "--root-dir",
                str(project),
                "--output",
                str(output),
                "--inject",
                str(missing),
            ],
        )
        assert rc == 1
        captured = capsys.readouterr()  # type: ignore[union-attr]
        assert "file not found" in captured.out


class TestPreCommitLifecycle:
    """Integration test simulating a realistic pre-commit hook lifecycle."""

    def test_full_lifecycle(self, tmp_path: Path) -> None:
        project: Path = tmp_path / "myproject"
        src: Path = project / "src"
        src.mkdir(parents=True)

        # --- Step 1: Create initial project with README ---
        (src / "__init__.py").write_text(
            '"""My project source package."""\n',
            encoding="utf-8",
        )
        (src / "app.py").write_text(
            '"""Application entry point."""\n',
            encoding="utf-8",
        )
        readme: Path = project / "README.md"
        readme.write_text(
            "# My Project\n\n"
            "<!-- content-tree -->\n"
            "<!-- /content-tree -->\n"
            "\n"
            "## License\nMIT\n",
            encoding="utf-8",
        )
        output: Path = project / "content_tree.md"

        # --- Step 2: Initialise git repo and make first commit ---
        _git(project, "init")
        _git(project, "add", ".")
        _git(
            project,
            "-c",
            "user.name=Test",
            "-c",
            "user.email=test@test.com",
            "commit",
            "-m",
            "initial",
        )

        # --- Step 3: First hook run (as pre-commit would invoke it) ---
        rc: int = main(
            [
                "--root-dir",
                str(project),
                "--output",
                str(output),
                "--inject",
                str(readme),
                "--docstrings",
            ],
        )
        assert rc == 1, "First run should detect changes"
        assert output.exists()

        tree_text: str = output.read_text(encoding="utf-8")
        assert "src/" in tree_text
        assert "app.py" in tree_text
        assert "# Application entry point." in tree_text
        # __init__.py docstring is promoted to directory line
        assert "src/  # My project source package." in tree_text
        assert "__init__.py" not in tree_text

        readme_text: str = readme.read_text(encoding="utf-8")
        assert "app.py" in readme_text
        assert readme_text.startswith("# My Project\n")
        assert readme_text.endswith("## License\nMIT\n")

        # --- Step 4: Idempotent re-run — no changes expected ---
        rc = main(
            [
                "--root-dir",
                str(project),
                "--output",
                str(output),
                "--inject",
                str(readme),
                "--docstrings",
            ],
        )
        assert rc == 0, "Second run should be a no-op"

        # --- Step 5: Add a new file, stage it, and re-run ---
        (src / "utils.py").write_text(
            '"""Shared utilities."""\n',
            encoding="utf-8",
        )
        _git(project, "add", str(src / "utils.py"))

        rc = main(
            [
                "--root-dir",
                str(project),
                "--output",
                str(output),
                "--inject",
                str(readme),
                "--docstrings",
            ],
        )
        assert rc == 1, "Third run should detect the new file"

        updated_tree: str = output.read_text(encoding="utf-8")
        assert "utils.py" in updated_tree
        assert "# Shared utilities." in updated_tree
        # Previous files still present (full tree, not filtered)
        assert "app.py" in updated_tree

        updated_readme: str = readme.read_text(encoding="utf-8")
        assert "utils.py" in updated_readme

        # --- Step 6: Untracked files must NOT appear ---
        (src / "scratch.py").write_text("# temp\n", encoding="utf-8")
        rc = main(
            [
                "--root-dir",
                str(project),
                "--output",
                str(output),
                "--docstrings",
            ],
        )
        scratch_tree: str = output.read_text(encoding="utf-8")
        assert "scratch.py" not in scratch_tree, (
            "Untracked files should be excluded"
        )
