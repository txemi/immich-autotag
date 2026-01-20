# Development version identifier
from .version import __git_commit__, __version__

# Re-export for package consumers
__all__ = ["__git_commit__", "__version__"]
