import sys
from pathlib import Path

def detect_venv_python() -> str:
    """Detect the virtual environment Python binary, fallback to sys.executable."""
    repo_root = Path(__file__).resolve().parent.parent.parent.parent
    venv_python = repo_root / '.venv' / 'bin' / 'python'
    if venv_python.exists():
        return str(venv_python)
    return sys.executable
