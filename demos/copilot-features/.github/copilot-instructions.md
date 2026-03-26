<!-- # Copilot Instructions

- Disallow magic numbers; use named constants.

## Rename Plan: `chroma_` → `chroma_`

### Step 1 — Backup
Before touching any files, create a restore point:
- Run `git checkout -b chore/globex-to-chroma-rename`
- Tag the last known-good commit: `git tag v-pre-rename`
- The branch itself acts as the primary rollback target.

### Step 2 — Dry Run (verify scope)
Run the rename script in `--check` mode to preview every change without writing:
- Run `python cli/rename.py --path . --check`
- Confirm it touches only the 12 known files and skips `.git/`, `__pycache__/`, and binary files.

### Step 3 — Execute & Test
Apply the rename, then immediately run the full test suite:
- Run `python cli/rename.py --path .`
- Run `python -m pytest -q` — all tests must pass before proceeding.
- Rename covers: file names, symbol identifiers, string literals, config keys, and import paths.

### Step 4 — CI Gate
A GitHub Actions workflow enforces the rename is complete and tests stay green:
- Run `pytest -q` on every push/PR.
- Fail the build if any `chroma_` identifier survives: `grep -r "chroma_" --include="*.py" --include="*.yaml" --include="*.md" --exclude-dir=".git" .`

### Step 5 — Rollback
If anything goes wrong:
- **Before merge**: `git checkout main && git branch -D chore/globex-to-chroma-rename`
- **After merge**: `git revert <merge-commit-sha> && git push origin main`
- **Automated**: `python cli/revert.py --path .` (inverse of rename.py: `chroma_` → `chroma_`) -->
