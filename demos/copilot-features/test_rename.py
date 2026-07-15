"""Tests for rename.py — covers content replacement, file renaming,
binary-file skipping, exclusion rules, and --dry-run / --check mode."""

from __future__ import annotations

import struct
from pathlib import Path

import pytest

from rename import (
    EXCLUDED_DIRS,
    SOURCE_PREFIX,
    TARGET_PREFIX,
    Summary,
    is_excluded,
    parse_args,
    rename_paths,
    replace_in_file,
    run,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_binary(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    # A valid PNG header followed by random bytes — definitely not UTF-8 decodable.
    path.write_bytes(b"\x89PNG\r\n\x1a\n" + struct.pack(">I", 0xDEADBEEF))


# ---------------------------------------------------------------------------
# is_excluded
# ---------------------------------------------------------------------------

class TestIsExcluded:
    def test_normal_file_is_not_excluded(self, tmp_path: Path) -> None:
        f = tmp_path / "src" / "globex_service.py"
        assert not is_excluded(f, tmp_path)

    @pytest.mark.parametrize("excluded_dir", sorted(EXCLUDED_DIRS))
    def test_excluded_dirs_are_skipped(self, tmp_path: Path, excluded_dir: str) -> None:
        f = tmp_path / excluded_dir / "some_file.py"
        assert is_excluded(f, tmp_path)

    def test_nested_excluded_dir(self, tmp_path: Path) -> None:
        f = tmp_path / "packages" / "node_modules" / "lodash" / "index.js"
        assert is_excluded(f, tmp_path)

    def test_path_outside_root_is_excluded(self, tmp_path: Path) -> None:
        other = tmp_path.parent / "other_dir" / "file.py"
        assert is_excluded(other, tmp_path)


# ---------------------------------------------------------------------------
# replace_in_file — content replacement
# ---------------------------------------------------------------------------

class TestReplaceInFile:
    def test_replaces_prefix_in_content(self, tmp_path: Path) -> None:
        f = tmp_path / "service.py"
        write(f, "class globex_Service:\n    def globex_run(self): pass\n")
        summary = Summary()

        replace_in_file(f, summary, dry_run=False)

        assert TARGET_PREFIX in f.read_text(encoding="utf-8")
        assert SOURCE_PREFIX not in f.read_text(encoding="utf-8")

    def test_counts_multiple_occurrences(self, tmp_path: Path) -> None:
        f = tmp_path / "utils.py"
        write(f, "globex_a = globex_b = globex_c = 1\n")
        summary = Summary()

        replace_in_file(f, summary, dry_run=False)

        assert summary.symbol_replacements == 3
        assert summary.files_updated == 1

    def test_untouched_file_not_counted_as_updated(self, tmp_path: Path) -> None:
        f = tmp_path / "clean.py"
        write(f, "def hello(): return 'world'\n")
        summary = Summary()

        replace_in_file(f, summary, dry_run=False)

        assert summary.files_updated == 0
        assert summary.symbol_replacements == 0
        assert summary.files_scanned == 1

    def test_increments_files_scanned(self, tmp_path: Path) -> None:
        f = tmp_path / "a.py"
        write(f, "no match here\n")
        summary = Summary()
        replace_in_file(f, summary, dry_run=False)
        assert summary.files_scanned == 1


# ---------------------------------------------------------------------------
# replace_in_file — binary / unreadable skip
# ---------------------------------------------------------------------------

class TestBinarySkip:
    def test_binary_file_is_skipped(self, tmp_path: Path) -> None:
        f = tmp_path / "image.png"
        write_binary(f)
        summary = Summary()

        replace_in_file(f, summary, dry_run=False)

        assert summary.binary_or_unreadable == 1
        assert summary.files_updated == 0
        # Original bytes must be intact.
        assert f.read_bytes().startswith(b"\x89PNG")

    def test_binary_file_scanned_but_not_updated(self, tmp_path: Path) -> None:
        f = tmp_path / "data.bin"
        write_binary(f)
        summary = Summary()

        replace_in_file(f, summary, dry_run=False)

        assert summary.files_scanned == 1
        assert summary.binary_or_unreadable == 1
        assert summary.symbol_replacements == 0


# ---------------------------------------------------------------------------
# rename_paths — file renaming
# ---------------------------------------------------------------------------

class TestRenamePaths:
    def test_file_with_source_prefix_is_renamed(self, tmp_path: Path) -> None:
        f = tmp_path / "globex_service.py"
        f.touch()
        summary = Summary()

        rename_paths(tmp_path, summary, dry_run=False)

        assert (tmp_path / "chroma_service.py").exists()
        assert not f.exists()
        assert summary.files_renamed == 1

    def test_dir_with_source_prefix_is_renamed(self, tmp_path: Path) -> None:
        d = tmp_path / "globex_utils"
        d.mkdir()
        (d / "helper.py").touch()
        summary = Summary()

        rename_paths(tmp_path, summary, dry_run=False)

        assert (tmp_path / "chroma_utils").exists()
        assert not d.exists()
        assert summary.directories_renamed == 1

    def test_deepest_paths_renamed_first(self, tmp_path: Path) -> None:
        parent = tmp_path / "globex_pkg"
        child = parent / "globex_module.py"
        parent.mkdir()
        child.touch()
        summary = Summary()

        rename_paths(tmp_path, summary, dry_run=False)

        assert (tmp_path / "chroma_pkg" / "chroma_module.py").exists()
        assert summary.files_renamed == 1
        assert summary.directories_renamed == 1

    def test_collision_recorded_as_error(self, tmp_path: Path) -> None:
        old = tmp_path / "globex_service.py"
        collision = tmp_path / "chroma_service.py"
        old.touch()
        collision.touch()
        summary = Summary()

        rename_paths(tmp_path, summary, dry_run=False)

        assert old.exists()          # not moved
        assert summary.errors == 1
        assert summary.files_renamed == 0

    def test_file_without_source_prefix_untouched(self, tmp_path: Path) -> None:
        f = tmp_path / "unrelated.py"
        f.touch()
        summary = Summary()

        rename_paths(tmp_path, summary, dry_run=False)

        assert f.exists()
        assert summary.files_renamed == 0

    def test_excluded_dir_contents_not_renamed(self, tmp_path: Path) -> None:
        git_dir = tmp_path / ".git" / "globex_config"
        git_dir.mkdir(parents=True)
        summary = Summary()

        rename_paths(tmp_path, summary, dry_run=False)

        assert git_dir.exists()
        assert summary.files_renamed == 0
        assert summary.directories_renamed == 0


# ---------------------------------------------------------------------------
# --dry-run / --check mode — nothing written to disk
# ---------------------------------------------------------------------------

class TestDryRun:
    def test_dry_run_does_not_modify_file_content(self, tmp_path: Path) -> None:
        f = tmp_path / "service.py"
        original = "class globex_Service: pass\n"
        write(f, original)
        summary = Summary()

        replace_in_file(f, summary, dry_run=True)

        assert f.read_text(encoding="utf-8") == original
        # But it should still be counted as a would-be update.
        assert summary.files_updated == 1
        assert summary.symbol_replacements == 1

    def test_dry_run_does_not_rename_files(self, tmp_path: Path) -> None:
        f = tmp_path / "globex_utils.py"
        f.touch()
        summary = Summary()

        rename_paths(tmp_path, summary, dry_run=True)

        assert f.exists()
        assert not (tmp_path / "chroma_utils.py").exists()
        assert summary.files_renamed == 1  # counted but not applied

    def test_run_dry_run_leaves_tree_unchanged(self, tmp_path: Path) -> None:
        f = tmp_path / "globex_service.py"
        original = "def globex_run(): pass\n"
        write(f, original)

        summary = run(tmp_path, dry_run=True)

        assert f.exists()
        assert f.read_text(encoding="utf-8") == original
        assert not (tmp_path / "chroma_service.py").exists()
        assert summary.files_updated == 1
        assert summary.files_renamed == 1

    def test_check_flag_parsed_as_dry_run(self) -> None:
        args = parse_args(["--check"])
        assert args.dry_run is True

    def test_dry_run_flag_parsed(self) -> None:
        args = parse_args(["--dry-run"])
        assert args.dry_run is True

    def test_no_flags_dry_run_is_false(self) -> None:
        args = parse_args([])
        assert args.dry_run is False


# ---------------------------------------------------------------------------
# parse_args
# ---------------------------------------------------------------------------

class TestParseArgs:
    def test_default_root_is_dot(self) -> None:
        args = parse_args([])
        assert args.root_path == "."

    def test_custom_root_path(self, tmp_path: Path) -> None:
        args = parse_args([str(tmp_path)])
        assert args.root_path == str(tmp_path)


# ---------------------------------------------------------------------------
# Integration: run() end-to-end
# ---------------------------------------------------------------------------

class TestRunIntegration:
    def test_full_rename_across_multiple_files(self, tmp_path: Path) -> None:
        write(tmp_path / "globex_service.py", "class globex_Service: pass\n")
        write(tmp_path / "globex_utils.py", "def globex_helper(): pass\n")
        write(tmp_path / "unrelated.py", "x = 1\n")

        summary = run(tmp_path, dry_run=False)

        assert (tmp_path / "chroma_service.py").exists()
        assert (tmp_path / "chroma_utils.py").exists()
        assert (tmp_path / "unrelated.py").exists()
        assert summary.files_renamed == 2
        assert summary.files_updated == 2
        assert summary.errors == 0

    def test_excluded_dirs_entirely_skipped(self, tmp_path: Path) -> None:
        for excluded in EXCLUDED_DIRS:
            write(tmp_path / excluded / "globex_secret.py", "globex_token = 'abc'\n")
        write(tmp_path / "globex_main.py", "globex_main()\n")

        summary = run(tmp_path, dry_run=False)

        assert summary.files_renamed == 1
        assert summary.files_updated == 1
        for excluded in EXCLUDED_DIRS:
            assert (tmp_path / excluded / "globex_secret.py").exists()

    def test_binary_files_are_skipped_end_to_end(self, tmp_path: Path) -> None:
        write_binary(tmp_path / "logo.png")
        write(tmp_path / "globex_config.yaml", "name: globex_app\n")

        summary = run(tmp_path, dry_run=False)

        assert summary.binary_or_unreadable == 1
        assert summary.files_updated == 1

    def test_summary_error_count_zero_on_clean_run(self, tmp_path: Path) -> None:
        write(tmp_path / "globex_a.py", "pass\n")
        summary = run(tmp_path, dry_run=False)
        assert summary.errors == 0
