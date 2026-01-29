# Versioning and Release Workflow for immich-autotag

## Versioning conventions (SemVer + Quality Gate)

This project follows [Semantic Versioning (SemVer)](https://semver.org/) with the following conventions:

- **MAJOR** (first digit): Incompatible changes or major functional jumps.
- **MINOR** (second digit): New important features, significant refactors, or user-visible changes.
- **PATCH** (third digit):
    - Incremented for minor fixes, hotfixes, or to mark Quality Gate points (e.g., when the STANDARD Quality Gate is passed or CI/CD is stabilized), even if there are no relevant functional changes.
    - The changelog only details functional or user-relevant changes (MAJOR/MINOR). PATCH increments for Quality Gate or maintenance do not require a detailed entry, unless you want to explicitly record the milestone.

**Note:** If you want to record a Quality Gate milestone, you may add a brief entry in the changelog, but it is not required to detail every PATCH if there are no functional changes.

For more details on how versions and Quality Gate milestones are reflected, see the header of [`../CHANGELOG.md`](../CHANGELOG.md).

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
