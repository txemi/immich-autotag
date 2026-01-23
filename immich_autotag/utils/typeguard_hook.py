"""
typeguard_hook.py

Utilidad para instalar el import hook de typeguard de forma segura y reutilizable.
"""

def install_typeguard_import_hook(package_name: str = "immich_autotag"):
    """
    Instala el import hook de typeguard para el paquete indicado.
    Si typeguard no está instalado, no hace nada.
    """
    try:
        import typeguard
        typeguard.install_import_hook(package_name)
    except ImportError:
        pass"""
Utilidad para instalar el import hook de typeguard de forma centralizada.
"""

def install_typeguard_import_hook(package_name: str = "immich_autotag"):
    """
    Instala el import hook de typeguard para el paquete indicado.
    Si typeguard no está instalado, no hace nada.
    """
    try:
        import typeguard
        typeguard.install_import_hook(package_name)
    except ImportError:
        pass
