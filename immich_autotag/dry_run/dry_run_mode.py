"""
Process-wide switch of the dry-run mode.

In a dry run the whole pipeline runs as usual (classification, temporary albums,
tags, date fixes, conversions, album dates, permissions), but nothing is written
to Immich: every write is recorded instead (see DryRunTransport).

The mode is on when activate_dry_run() was called (the ``--dry-run`` flag) or
when the environment variable IMMICH_AUTOTAG_DRY_RUN holds a true value. An
unrecognised value of the variable is an error, never a silent real run.
"""

from __future__ import annotations

import os

DRY_RUN_ENV_VAR = "IMMICH_AUTOTAG_DRY_RUN"

_TRUE_VALUES = frozenset({"1", "true", "yes", "on"})
_FALSE_VALUES = frozenset({"", "0", "false", "no", "off"})

_activated_by_flag = False


def dry_run_requested_by_env() -> bool:
    """Whether IMMICH_AUTOTAG_DRY_RUN asks for a dry run.

    Raises ValueError on a value that is neither true nor false, so that a typo
    stops the run instead of running it for real.
    """
    raw = os.environ.get(DRY_RUN_ENV_VAR, "").strip().lower()
    if raw in _TRUE_VALUES:
        return True
    if raw in _FALSE_VALUES:
        return False
    raise ValueError(
        f"Unrecognised value for {DRY_RUN_ENV_VAR}: {raw!r}. "
        f"Use one of {sorted(_TRUE_VALUES)} or {sorted(_FALSE_VALUES)}."
    )


def activate_dry_run() -> None:
    """Turns the dry-run mode on for this process (and its children)."""
    global _activated_by_flag
    _activated_by_flag = True
    os.environ[DRY_RUN_ENV_VAR] = "1"


def deactivate_dry_run() -> None:
    """Turns the dry-run mode off. Meant for tests."""
    global _activated_by_flag
    _activated_by_flag = False
    os.environ.pop(DRY_RUN_ENV_VAR, None)


def is_dry_run_active() -> bool:
    """Whether this process runs in dry-run mode."""
    return _activated_by_flag or dry_run_requested_by_env()
