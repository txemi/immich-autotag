def raise_if_development_mode(msg: str) -> None:
    """
    Raise RuntimeError with msg if in development mode.
    """
    if is_development_mode():
        raise RuntimeError(msg)


from immich_autotag.config._internal_types import ErrorHandlingMode
from immich_autotag.config.internal_config import DEFAULT_ERROR_MODE


def is_development_mode() -> bool:
    """
    Returns True if the current error mode is DEVELOPMENT or CRAZY_DEBUG.
    This indirection helps mypy avoid constant folding and false positives.
    """
    return DEFAULT_ERROR_MODE in (
        ErrorHandlingMode.DEVELOPMENT,
        ErrorHandlingMode.CRAZY_DEBUG,
    )
