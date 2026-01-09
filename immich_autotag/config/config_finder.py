import os
from pathlib import Path
import importlib.util
import yaml
from typing import Optional

def find_user_config():
    """
    Searches for user configuration following this priority:
    1. user_config.py in the repo (development mode)
    2. user_config.yaml in the repo (development mode)
    3. config.py in XDG_CONFIG_HOME/immich_autotag/
    4. config.yaml in XDG_CONFIG_HOME/immich_autotag/
    5. config.py in ~/.immich_autotag/
    6. config.yaml in ~/.immich_autotag/
    7. Environment variable IMMICH_AUTOTAG_CONFIG
    """
    # 1. user_config.py in the repo
    repo_py = Path(__file__).parent / "user_config.py"
    if repo_py.exists():
        return ("python", repo_py)
    # 2. user_config.yaml in the repo
    repo_yaml = Path(__file__).parent / "user_config.yaml"
    if repo_yaml.exists():
        return ("yaml", repo_yaml)
    # 3-4. XDG_CONFIG_HOME
    xdg_config_home = os.environ.get("XDG_CONFIG_HOME", str(Path.home() / ".config"))
    xdg_dir = Path(xdg_config_home) / "immich_autotag"
    xdg_py = xdg_dir / "config.py"
    if xdg_py.exists():
        return ("python", xdg_py)
    xdg_yaml = xdg_dir / "config.yaml"
    if xdg_yaml.exists():
        return ("yaml", xdg_yaml)
    # 5-6. Legacy ~/.immich_autotag
    legacy_dir = Path.home() / ".immich_autotag"
    legacy_py = legacy_dir / "config.py"
    if legacy_py.exists():
        return ("python", legacy_py)
    legacy_yaml = legacy_dir / "config.yaml"
    if legacy_yaml.exists():
        return ("yaml", legacy_yaml)
    # 7. Environment variable
    env_path = os.environ.get("IMMICH_AUTOTAG_CONFIG")
    if env_path:
        env_path = Path(env_path)
        if env_path.exists():
            if env_path.suffix == ".py":
                return ("python", env_path)
            elif env_path.suffix in (".yaml", ".yml"):
                return ("yaml", env_path)
    return (None, None)

def load_python_config(path: Path):
    """Dynamically loads a Python file that defines 'user_config' or 'config'"""
    spec = importlib.util.spec_from_file_location("user_config_module", str(path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    # Search for user_config or config
    if hasattr(module, "user_config"):
        return module.user_config
    elif hasattr(module, "config"):
        return module.config
    else:
        raise AttributeError(f"'user_config' or 'config' not found in {path}")

def load_yaml_config(path: Path):
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data
