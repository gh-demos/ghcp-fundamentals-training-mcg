"""CLI tool to rename globex_ to chroma_ across a codebase."""
import argparse
import logging
import os
import re
import sys

SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv"}
OLD = "globex_"
NEW = "chroma_"
OLD_CLASS = "Globex"
NEW_CLASS = "Chroma"

logging.basicConfig(format="%(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

TEXT_EXTENSIONS = {
    ".py", ".yaml", ".yml", ".md", ".txt", ".json", ".toml", ".cfg", ".ini", ".rst"
}


def _is_text_file(path: str) -> bool:
    _, ext = os.path.splitext(path)
    return ext.lower() in TEXT_EXTENSIONS


def _replace_content(text: str) -> str:
    text = text.replace(OLD, NEW)
    text = re.sub(r"\bGlobex", NEW_CLASS, text)
    return text


def _rename_path(path: str) -> str:
    head, tail = os.path.split(path)
    new_tail = tail.replace(OLD, NEW).replace(OLD_CLASS, NEW_CLASS)
    return os.path.join(head, new_tail) if new_tail != tail else path


def process(root: str, check: bool) -> None:
    content_changes: list[tuple[str, int]] = []
    file_renames: list[tuple[str, str]] = []
    skipped_binary: list[str] = []

    for dirpath, dirnames, filenames in os.walk(root, topdown=False):
        # With topdown=False, dirnames[:] pruning does not prevent descent;
        # check every path component explicitly instead.
        rel_parts = set(os.path.relpath(dirpath, root).split(os.sep))
        if rel_parts & SKIP_DIRS:
            continue
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]

        for fname in filenames:
            fpath = os.path.join(dirpath, fname)
            rel = os.path.relpath(fpath, root)

            if _is_text_file(fpath):
                try:
                    with open(fpath, "r", encoding="utf-8") as fh:
                        original = fh.read()
                except (UnicodeDecodeError, PermissionError):
                    skipped_binary.append(rel)
                    continue

                replaced = _replace_content(original)
                if replaced != original:
                    changed_lines = sum(
                        1 for a, b in zip(original.splitlines(), replaced.splitlines()) if a != b
                    )
                    content_changes.append((rel, changed_lines))
                    if not check:
                        with open(fpath, "w", encoding="utf-8") as fh:
                            fh.write(replaced)
            else:
                skipped_binary.append(rel)

            new_path = _rename_path(fpath)
            if new_path != fpath:
                old_rel = os.path.relpath(fpath, root)
                new_rel = os.path.relpath(new_path, root)
                file_renames.append((old_rel, new_rel))
                if not check:
                    os.rename(fpath, new_path)

        new_dirpath = _rename_path(dirpath)
        if new_dirpath != dirpath:
            old_rel = os.path.relpath(dirpath, root)
            new_rel = os.path.relpath(new_dirpath, root)
            file_renames.append((f"{old_rel}/", f"{new_rel}/"))
            if not check:
                os.rename(dirpath, new_dirpath)

    mode = "[DRY RUN]" if check else "[APPLIED]"
    logger.info("\n%s Rename summary", mode)
    logger.info("=" * 60)

    if content_changes:
        logger.info("\nContent changes (%d file(s)):", len(content_changes))
        logger.info("  %-50s  %s", "File", "Lines changed")
        logger.info("  " + "-" * 55)
        for path, lines in content_changes:
            logger.info("  %-50s  %d", path, lines)
    else:
        logger.info("\nNo content changes needed.")

    if file_renames:
        logger.info("\nFile/dir renames (%d):", len(file_renames))
        for old, new in file_renames:
            logger.info("  %s  ->  %s", old, new)
    else:
        logger.info("\nNo file renames needed.")

    if skipped_binary:
        logger.info("\nSkipped (binary/unreadable) (%d):", len(skipped_binary))
        for p in skipped_binary:
            logger.info("  %s", p)

    logger.info("\nTotal: %d content change(s), %d rename(s)", len(content_changes), len(file_renames))
    if check:
        logger.info("\nRun without --check to apply changes.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Rename identifiers across a codebase.")
    parser.add_argument("--path", default=".", help="Root directory to process (default: .)")
    parser.add_argument("--check", action="store_true", help="Dry run -- preview changes without writing")
    args = parser.parse_args()

    root = os.path.abspath(args.path)
    if not os.path.isdir(root):
        logger.error("Path not found: %s", root)
        sys.exit(1)

    process(root, check=args.check)


if __name__ == "__main__":
    main()
