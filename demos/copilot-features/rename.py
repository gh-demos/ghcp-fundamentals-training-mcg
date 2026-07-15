#!/usr/bin/env python3
"""Recursively rename globex_ to chroma_ in file contents and file/directory names.

Usage:
    python rename.py [root_path] [--dry-run | --check]

``--dry-run`` and ``--check`` are equivalent: they preview changes without
writing or renaming anything on disk.
"""

from __future__ import annotations

import argparse
import logging
import os
from pathlib import Path
from typing import Iterable

SOURCE_PREFIX = "globex_"
TARGET_PREFIX = "chroma_"
EXCLUDED_DIRS = {".git", "node_modules"}
DEFAULT_ENCODING = "utf-8"

logger = logging.getLogger(__name__)


class Summary:
    def __init__(self) -> None:
        self.files_scanned = 0
        self.files_updated = 0
        self.symbol_replacements = 0
        self.files_renamed = 0
        self.directories_renamed = 0
        self.binary_or_unreadable = 0
        self.errors = 0


def is_excluded(path: Path, root: Path) -> bool:
    try:
        relative_parts = path.relative_to(root).parts
    except ValueError:
        return True
    return any(part in EXCLUDED_DIRS for part in relative_parts)


def iter_files(root: Path) -> Iterable[Path]:
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in EXCLUDED_DIRS]
        for filename in filenames:
            yield Path(dirpath) / filename


def replace_in_file(file_path: Path, summary: Summary, dry_run: bool) -> None:
    summary.files_scanned += 1
    try:
        original = file_path.read_text(encoding=DEFAULT_ENCODING)
    except (UnicodeDecodeError, OSError):
        summary.binary_or_unreadable += 1
        return

    replacement_count = original.count(SOURCE_PREFIX)
    if replacement_count == 0:
        return

    updated = original.replace(SOURCE_PREFIX, TARGET_PREFIX)
    if not dry_run:
        try:
            file_path.write_text(updated, encoding=DEFAULT_ENCODING)
        except OSError as exc:
            summary.errors += 1
            logger.error("ERROR writing %s: %s", file_path, exc)
            return

    summary.files_updated += 1
    summary.symbol_replacements += replacement_count


def rename_paths(root: Path, summary: Summary, dry_run: bool) -> None:
    all_paths = [
        path
        for path in root.rglob("*")
        if not is_excluded(path, root) and SOURCE_PREFIX in path.name
    ]

    # Rename deepest paths first so children move before parents.
    all_paths.sort(key=lambda p: len(p.parts), reverse=True)

    for old_path in all_paths:
        new_name = old_path.name.replace(SOURCE_PREFIX, TARGET_PREFIX)
        new_path = old_path.with_name(new_name)

        if new_path.exists():
            summary.errors += 1
            logger.warning("SKIP collision: %s -> %s", old_path, new_path)
            continue

        try:
            is_dir = old_path.is_dir()
            if not dry_run:
                old_path.rename(new_path)
            if is_dir:
                summary.directories_renamed += 1
            else:
                summary.files_renamed += 1
            logger.info("RENAMED: %s -> %s", old_path, new_path)
        except OSError as exc:
            summary.errors += 1
            logger.error("ERROR renaming %s: %s", old_path, exc)


def run(root: Path, dry_run: bool) -> Summary:
    summary = Summary()

    logger.info("Root: %s", root)
    logger.info("Dry run: %s", dry_run)
    logger.info("Replace: %s -> %s", SOURCE_PREFIX, TARGET_PREFIX)
    logger.info("Excluded dirs: %s", ", ".join(sorted(EXCLUDED_DIRS)))

    for file_path in iter_files(root):
        replace_in_file(file_path, summary, dry_run)

    rename_paths(root, summary, dry_run)
    return summary


def print_summary(summary: Summary) -> None:
    logger.info("\nSummary")
    logger.info("Files scanned:          %d", summary.files_scanned)
    logger.info("Files updated:          %d", summary.files_updated)
    logger.info("Symbol replacements:    %d", summary.symbol_replacements)
    logger.info("Files renamed:          %d", summary.files_renamed)
    logger.info("Directories renamed:    %d", summary.directories_renamed)
    logger.info("Binary/unreadable skip: %d", summary.binary_or_unreadable)
    logger.info("Errors:                 %d", summary.errors)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Recursively rename globex_ to chroma_ in symbols and filenames."
    )
    parser.add_argument(
        "root_path",
        nargs="?",
        default=".",
        help="Root folder to process. Defaults to current directory.",
    )
    parser.add_argument(
        "--dry-run",
        "--check",
        dest="dry_run",
        action="store_true",
        help="Preview changes without writing to disk (also accepted as --check).",
    )
    return parser.parse_args(argv)


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    args = parse_args()
    root = Path(args.root_path).resolve()

    if not root.exists() or not root.is_dir():
        logger.error("Invalid root directory: %s", root)
        return 1

    summary = run(root, args.dry_run)
    print_summary(summary)
    return 0 if summary.errors == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
