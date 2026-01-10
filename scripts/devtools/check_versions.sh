#!/bin/bash
# check_versions.sh
# Shows the version in pyproject.toml, the latest tag, and git status

set -e 

echo "Version in pyproject.toml:"
grep '^version' pyproject.toml || echo "Not found"
echo
LATEST_TAG=$(git describe --tags --abbrev=0 2>/dev/null)
echo "Latest git tag: $LATEST_TAG"
echo
GIT_DESCRIBE=$(git describe --tags --always --dirty)
echo "git describe: $GIT_DESCRIBE"
echo
if [[ -n "$LATEST_TAG" ]]; then
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
    echo "There are no tags in the repository."
    exit 1
fi
