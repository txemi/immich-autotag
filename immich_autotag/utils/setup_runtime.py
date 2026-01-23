"""
setup_runtime.py

Utilidades para inicializar el entorno de ejecución: logging duplicado y exception hook global.
"""


def setup_logging_and_exceptions():
    """
    Inicializa el duplicado de logs (stdout/stderr) y el exception hook global.
    """
    from immich_autotag.utils.exception_hook import setup_exception_hook
    from immich_autotag.utils.tee_logging import setup_tee_logging

    setup_tee_logging()
    setup_exception_hook()
