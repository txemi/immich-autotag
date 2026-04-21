#!/bin/bash
# check_versions.sh
# Shows the version in pyproject.toml, the latest tag, and git status

set -e

echo "Version in pyproject.toml:"
grep '^version' pyproject.toml || echo "Not found"
echo
# Prefer the latest semver tag (vX.Y.Z or X.Y.Z). If none found, fall back to any tag.
LATEST_TAG=$(git for-each-ref --sort=-creatordate --format '%(refname:short)' refs/tags | grep -E '^v?[0-9]+\.[0-9]+\.[0-9]+$' | head -n1 || true)
if [ -z "$LATEST_TAG" ]; then
	# fallback: pick any tag if no semver tag exists
	LATEST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || "")
fi
echo "Latest git tag: $LATEST_TAG"
echo
GIT_DESCRIBE=$(git describe --tags --always --dirty)
echo "git describe: $GIT_DESCRIBE"
echo
if [[ -n "$LATEST_TAG" ]]; then
	# Only perform strict comparison if the latest tag looks like a semantic version
	if echo "$LATEST_TAG" | grep -Eq '^v?[0-9]+\.[0-9]+\.[0-9]+$'; then
		TOML_VERSION=$(grep '^version' pyproject.toml | head -1 | cut -d'=' -f2 | tr -d ' "')
		# Remove the 'v' prefix if it exists in the tag
		TAG_VERSION=${LATEST_TAG#v}
		if [[ "$TOML_VERSION" != "$TAG_VERSION" ]]; then
			echo -e "\e[31mWARNING! The version in pyproject.toml ($TOML_VERSION) and the latest git tag ($LATEST_TAG) DO NOT match.\e[0m" >&2
			exit 1
		else
			echo -e "\e[32mThe version in pyproject.toml and the latest git tag match.\e[0m"
		fi
	else
		echo "Note: Latest tag ($LATEST_TAG) does not match semantic-version pattern; skipping strict comparison."
		exit 0
	fi
else
	echo "No tags found in the repository; skipping version/tag comparison."
	exit 0
fi
