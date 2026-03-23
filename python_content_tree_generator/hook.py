from __future__ import annotations

import argparse
from pathlib import Path

from python_content_tree_generator.update_contents_md import (
    build_content_tree,
    generate_markdown,
    inject_into_file,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Generate a content tree markdown file for a Python project.",
    )
    parser.add_argument(
        "--root-dir",
        required=True,
        type=Path,
        help="Root directory of the Python project to scan.",
    )
    parser.add_argument(
        "--output",
        default="content_tree.md",
        type=Path,
        help="Output markdown file (default: content_tree.md).",
    )
    parser.add_argument(
        "--ignore",
        nargs="*",
        default=[],
        help="File names to ignore.",
    )
    parser.add_argument(
        "--docstrings",
        action="store_true",
        help="Include first-line docstrings for Python files.",
    )
    parser.add_argument(
        "--inject",
        nargs="*",
        type=Path,
        default=[],
        help="Files to inject the tree into (between <!-- content-tree --> markers).",
    )
    args: argparse.Namespace = parser.parse_args(argv)

    ignore: tuple[str, ...] = tuple(args.ignore) if args.ignore else ()
    tree = build_content_tree(
        args.root_dir,
        ignore_files=ignore,
        docstrings=args.docstrings,
    )
    root_name: str = args.root_dir.resolve().name
    new_content: str = generate_markdown(tree, root_name)

    changed: bool = False

    # Write standalone output file
    if args.output.exists():
        existing: str = args.output.read_text(encoding="utf-8")
        if existing != new_content:
            args.output.write_text(new_content, encoding="utf-8")
            print(f"Content tree updated: {args.output}")
            changed = True
    else:
        args.output.write_text(new_content, encoding="utf-8")
        print(f"Content tree updated: {args.output}")
        changed = True

    # Inject into files with markers
    for inject_path in args.inject:
        try:
            if inject_into_file(inject_path, new_content):
                print(f"Content tree injected into: {inject_path}")
                changed = True
        except (FileNotFoundError, ValueError) as exc:
            print(f"Error: {exc}")
            return 1

    return 1 if changed else 0


if __name__ == "__main__":
    raise SystemExit(main())
