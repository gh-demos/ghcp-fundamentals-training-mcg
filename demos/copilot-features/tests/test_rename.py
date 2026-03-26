"""Tests for cli/rename.py — content replacement, binary skipping, and --check dry-run."""
import os
import sys
import pytest

# Ensure the repo root is on the path so `cli.rename` can be imported
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from cli.rename import _replace_content, _rename_path, process


# ---------------------------------------------------------------------------
# _replace_content — symbol substitution inside text
# ---------------------------------------------------------------------------

def test_replace_content_snake_case():
    assert _replace_content("def globex_init(): pass") == "def chroma_init(): pass"


def test_replace_content_pascal_case():
    assert _replace_content("class GlobexService:") == "class ChromaService:"


def test_replace_content_mixed():
    src = "from globex_utils import GlobexHelper\nglobex_setting: value"
    out = _replace_content(src)
    assert "globex_" not in out
    assert "Globex" not in out
    assert "chroma_utils" in out
    assert "ChromaHelper" in out


def test_replace_content_no_change():
    src = "print('hello world')"
    assert _replace_content(src) == src


def test_replace_content_partial_word_not_affected():
    """'Globex' inside a longer word should not be touched by word-boundary regex."""
    src = "SuperGlobexThing"
    # 'Globex' is not at a word boundary here, so it stays
    assert _replace_content(src) == "SuperGlobexThing"


# ---------------------------------------------------------------------------
# _rename_path — file / directory name substitution
# ---------------------------------------------------------------------------

def test_rename_path_file():
    assert _rename_path("/project/app/globex_service.py") == "/project/app/chroma_service.py"


def test_rename_path_dir():
    assert _rename_path("/project/globex_module") == "/project/chroma_module"


def test_rename_path_no_match():
    path = "/project/app/main.py"
    assert _rename_path(path) == path


def test_rename_path_pascal():
    assert _rename_path("/project/GlobexUtils.py") == "/project/ChromaUtils.py"


# ---------------------------------------------------------------------------
# process() — integration: content is rewritten on disk
# ---------------------------------------------------------------------------

def test_process_rewrites_file_content(tmp_path):
    src = tmp_path / "globex_module.py"
    src.write_text("def globex_run(): return True\n", encoding="utf-8")

    process(str(tmp_path), check=False)

    renamed = tmp_path / "chroma_module.py"
    assert renamed.exists(), "File should have been renamed"
    assert not src.exists(), "Old file should be gone"
    assert "chroma_run" in renamed.read_text(encoding="utf-8")
    assert "globex_" not in renamed.read_text(encoding="utf-8")


def test_process_multiple_files(tmp_path):
    (tmp_path / "globex_a.py").write_text("globex_foo = 1\n", encoding="utf-8")
    (tmp_path / "globex_b.yaml").write_text("globex_key: value\n", encoding="utf-8")

    process(str(tmp_path), check=False)

    assert (tmp_path / "chroma_a.py").exists()
    assert (tmp_path / "chroma_b.yaml").exists()
    assert "chroma_foo" in (tmp_path / "chroma_a.py").read_text(encoding="utf-8")
    assert "chroma_key" in (tmp_path / "chroma_b.yaml").read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# process() — binary / unreadable files are skipped
# ---------------------------------------------------------------------------

def test_process_skips_binary_files(tmp_path):
    binary = tmp_path / "globex_data.bin"
    original_bytes = b"\x00\x01\x02\xff\xfe globex_ \x00"
    binary.write_bytes(original_bytes)

    process(str(tmp_path), check=False)

    # File name should be renamed; raw bytes must be unchanged
    renamed = tmp_path / "chroma_data.bin"
    assert renamed.exists(), "Binary file name should be renamed"
    assert not binary.exists(), "Old binary name should be gone"
    assert renamed.read_bytes() == original_bytes, "Binary content must not be modified"


def test_process_skips_unknown_extension(tmp_path):
    unknown = tmp_path / "globex_file.xyz"
    original_bytes = b"globex_ binary content \x80\x81"
    unknown.write_bytes(original_bytes)

    process(str(tmp_path), check=False)

    # .xyz is not a text extension — content must not change, but name is renamed
    renamed = tmp_path / "chroma_file.xyz"
    assert renamed.exists(), ".xyz file name should still be renamed"
    assert not unknown.exists(), "Old .xyz name should be gone"
    assert renamed.read_bytes() == original_bytes, ".xyz content must not be modified"


# ---------------------------------------------------------------------------
# process() — --check dry-run: nothing is written or renamed
# ---------------------------------------------------------------------------

def test_process_check_does_not_write(tmp_path):
    src = tmp_path / "globex_service.py"
    original = "def globex_init(): pass\n"
    src.write_text(original, encoding="utf-8")

    process(str(tmp_path), check=True)

    # File must still exist under the OLD name with ORIGINAL content
    assert src.exists(), "Dry-run must not rename the file"
    assert src.read_text(encoding="utf-8") == original, "Dry-run must not modify content"
    assert not (tmp_path / "chroma_service.py").exists(), "Dry-run must not create new file"


def test_process_check_no_side_effects_multi(tmp_path):
    files = {
        "globex_a.py": "x = globex_a_val\n",
        "globex_b.md": "# GlobexDocs\n",
    }
    for name, content in files.items():
        (tmp_path / name).write_text(content, encoding="utf-8")

    process(str(tmp_path), check=True)

    for name, content in files.items():
        path = tmp_path / name
        assert path.exists(), f"Dry-run must not rename {name}"
        assert path.read_text(encoding="utf-8") == content, f"Dry-run must not modify {name}"


# ---------------------------------------------------------------------------
# process() — skip dirs (.git, node_modules)
# ---------------------------------------------------------------------------

def test_process_skips_git_directory(tmp_path):
    git_dir = tmp_path / ".git"
    git_dir.mkdir()
    secret = git_dir / "globex_config"
    secret.write_text("globex_secret=1\n", encoding="utf-8")

    process(str(tmp_path), check=False)

    # File inside .git must be untouched
    assert secret.exists(), "Files inside .git must not be touched"
    assert "globex_" in secret.read_text(encoding="utf-8")


def test_process_skips_node_modules(tmp_path):
    nm = tmp_path / "node_modules"
    nm.mkdir()
    pkg = nm / "globex_pkg.js"
    pkg.write_text("module.exports = {};\n", encoding="utf-8")

    process(str(tmp_path), check=False)

    assert pkg.exists(), "Files inside node_modules must not be touched"
