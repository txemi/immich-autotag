"""
Utility functions to build links to GitHub documentation according to the running version/commit.
"""

from immich_autotag import __git_commit__, __git_describe__


def get_git_ref():
    """
    Returns the git reference identifier (short commit or describe) of the running version.
    Tries to use __git_describe__, if not available uses __git_commit__, otherwise 'main'.
    """
    return __git_describe__ or __git_commit__ or "main"


def github_doc_url(path: str, ref: str | None = None) -> str:
    """
    Builds a link to the documentation in GitHub using the current git reference.
    path: relative path within the repo (e.g., 'immich_autotag/config/models.py')
    ref: branch, tag or commit (defaults to get_git_ref())
    """
    if ref is None:
        ref = get_git_ref()
    return f"https://github.com/txemi/immich-autotag/blob/{ref}/{path}"
