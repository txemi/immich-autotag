"""
setup_runtime_typeguard.py

Utilidad para activar typeguard globalmente en el paquete.
"""

def setup_typeguard_import_hook(package_name="immich_autotag"):
    """
    Activa el chequeo de tipos en tiempo de ejecución para todo el paquete indicado.
    Si typeguard no está instalado, no hace nada.
    """
    try:
        import typeguard
        typeguard.install_import_hook(package_name)
    except ImportError:
        pass
