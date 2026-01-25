"""
Utilidad para marcar rutas deprecadas o no alcanzables en el código.
"""

class InternalDeprecationError(Exception):
    """
    Excepción para indicar que se ha ejecutado una ruta deprecada o no válida.
    """
    pass

def raise_deprecated_path(description: str) -> None:
    """
    Lanza una excepción InternalDeprecationError con una descripción informativa.
    Uso: llamar en puntos del código que no deberían ejecutarse.
    """
    raise InternalDeprecationError(f"DEPRECATED PATH: {description}")
