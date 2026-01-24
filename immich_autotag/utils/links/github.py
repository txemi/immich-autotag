"""
Funciones utilitarias para construir enlaces a la documentación de GitHub según la versión/commit en ejecución.
"""

from immich_autotag import __git_commit__, __git_describe__


def get_git_ref():
    """
    Devuelve el identificador de referencia git (commit corto o describe) de la versión en ejecución.
    Intenta usar __git_describe__, si no existe usa __git_commit__, si no, 'main'.
    """
    return __git_describe__ or __git_commit__ or "main"


def github_doc_url(path: str, ref: str | None = None) -> str:
    """
    Construye un enlace a la documentación en GitHub usando la referencia git actual.
    path: ruta relativa dentro del repo (por ejemplo, 'immich_autotag/config/models.py')
    ref: rama, tag o commit (por defecto usa get_git_ref())
    """
    if ref is None:
        ref = get_git_ref()
    return f"https://github.com/txemi/immich-autotag/blob/{ref}/{path}"
