"""
typeguard_hook.py

Utility to install the typeguard import hook in a safe and reusable way.
"""


def install_typeguard_import_hook(package_name: str = "immich_autotag"):
    """
    Installs the typeguard import hook for the given package.
    If typeguard is not installed, does nothing.
    """
    try:
        import typeguard

        typeguard.install_import_hook(package_name)
    except ImportError:
        pass
