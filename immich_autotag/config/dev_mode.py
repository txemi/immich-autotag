from immich_autotag.config._internal_types import ErrorHandlingMode
from immich_autotag.config.internal_config import DEFAULT_ERROR_MODE


def is_crazy_debug_mode() -> bool:
    """
    Returns True if the current error mode is CRAZY_DEBUG.
    """
    return DEFAULT_ERROR_MODE == ErrorHandlingMode.CRAZY_DEBUG


def is_development_mode() -> bool:
    """
    Returns True if the current error mode is DEVELOPMENT or CRAZY_DEBUG.
    This indirection helps mypy avoid constant folding and false positives.
    """
    return DEFAULT_ERROR_MODE in (
        ErrorHandlingMode.DEVELOPMENT,
        ErrorHandlingMode.CRAZY_DEBUG,
    )


def raise_if_development_mode(msg: str) -> None:
    """
    Raise RuntimeError with msg if in development mode.
    """
    if is_development_mode():
        raise RuntimeError(msg)


def always_true_for_flow_control() -> bool:
    """
    Utility function for explicit flow control in exceptional situations.
    Always returns True. Use this in conditional branches where you want to
    forcibly raise exceptions or cut execution flow, but want to avoid linter
    warnings about dead code or unreachable branches.

    Example usage:
        if always_true_for_flow_control():
            raise RuntimeError("Forced exception for debugging or unreachable code.")

    This function is intentionally simple and will always survive refactors,
    so you can use it as a placeholder for future review or to mark code that
    should be revisited.
    """
    return True
