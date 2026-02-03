"""
Import hook for architecture checks (package entry point).
This module installs a custom import hook that checks every import
against a set of architectural rules.
"""

from immich_autotag.architecture_import import ArchitectureImportChecker


def install_architecture_import_hook():
    ArchitectureImportChecker.install_architecture_import_hook()


def setup_import_architecture_hook():
    """
    Setup architecture import hook. Call this early in your app initialization,
    similar to logging/typeguard setup.
    """
    install_architecture_import_hook()


def initialize_app():
    # ...existing initialization code (logging, typeguard, etc.)...
    setup_import_architecture_hook()
    # ...other hooks or checks...


if __name__ == "__main__":
    initialize_app()
    print("math imported successfully")
