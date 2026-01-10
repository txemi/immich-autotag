# Versioning and Release Workflow for immich-autotag

## Workflow Consensus (2026-01-10)

### Source of Truth
- The **version in pyproject.toml** is the canonical version for Python packaging and distribution.
- The **git tag** must always match the version in pyproject.toml and be created on the commit that updates pyproject.toml.
- The **code version file** (`immich_autotag/version.py`) must reflect the version, git commit, and a human-friendly git describe string for traceability.

### Release Steps
1. **Update `pyproject.toml`** to the new version.
2. **Commit** the change: `git commit -am "Bump version to <new_version>"`
3. **Create the git tag**: `git tag v<new_version>`
4. **Run the version check script** to ensure consistency.
5. **Run the version info update script** to update `version.py` with:
    - `__version__` (from pyproject.toml)
    - `__git_commit__` (from git)
    - `__git_describe__` (from `git describe`)
6. **Commit the updated version.py**: `git commit -am "Update version info for <new_version>"`
7. **Push** commits and tag: `git push && git push origin v<new_version>`

### Why this workflow?
- Ensures PyPI, users, and developers all see the same version.
- Guarantees reproducibility and traceability for support and debugging.
- The `git describe` string is included for easy human comparison and communication.

### Scripts Involved
- `scripts/devtools/check_versions.sh`: Aborts if pyproject.toml and git tag are not consistent.
- `scripts/devtools/update_version_info.sh`: Updates `immich_autotag/version.py` with version, commit, and git describe.
- `scripts/devtools/release.sh`: Automates the workflow above.

---

## Example `immich_autotag/version.py`
```python
# This file is auto-updated during release
__version__ = "0.21.0"
__git_commit__ = "33c33da"
__git_describe__ = "v0.21.0-0-g33c33da"
```

---

## Human-friendly version string
- The `__git_describe__` field is included for support, user reporting, and easy comparison.
- Example: `v0.21.0-0-g33c33da` (tag, number of commits since tag, commit hash)

---

## All scripts have been/will be updated to follow this workflow and abort on inconsistency.
