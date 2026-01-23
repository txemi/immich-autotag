"""
setup_runtime.py

Utilities to initialize the runtime environment: duplicate logging and global exception hook.
"""


def setup_logging_and_exceptions():
    """
    Initializes duplicate logging (stdout/stderr) and the global exception hook.
    """
    from immich_autotag.utils.exception_hook import setup_exception_hook
    from immich_autotag.utils.tee_logging import setup_tee_logging

    setup_tee_logging()
    setup_exception_hook()
