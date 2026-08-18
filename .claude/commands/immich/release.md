Execute a release for immich-autotag.

## Steps

1. If the user provided a version number as argument, use it. Otherwise ask: "Which version do you want to publish? (current: `cat pyproject.toml | grep ^version`)"

2. Check preconditions:
   - Run `git status` — abort if there are uncommitted changes.
   - Run `git branch --show-current` — warn (but don't abort) if we're on `main` or `develop`, since releases are normally done from feature branches.

3. Show a summary and ask for confirmation before proceeding:
   - Current branch
   - New version
   - What will happen: pyproject.toml bump, tag vX.Y.Z, push → GitHub Actions → PyPI + Docker

4. Run: `bash scripts/devtools/release.sh <version>`

5. Verify success:
   - Confirm the tag appears in `git tag | tail -5`
   - Remind the user to check GitHub Actions at https://github.com/txemi/immich-autotag/actions
