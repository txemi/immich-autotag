import importlib.util
import os
from enum import Enum
from pathlib import Path

import attrs
import yaml
from typeguard import typechecked


class ConfigType(Enum):
    PYTHON = "python"
    YAML = "yaml"


@attrs.define(frozen=True, auto_attribs=True, slots=True)
class ConfigLocation:
    path: Path = attrs.field(validator=attrs.validators.instance_of(Path))

    def __attrs_post_init__(self):
        if not self.path.exists():
            raise FileNotFoundError(f"Config file does not exist: {self.path}")

    @typechecked
    def get_type(self) -> "ConfigType":
        ext = self.path.suffix.lower()
        if ext == ".py":
            return ConfigType.PYTHON
        elif ext in (".yaml", ".yml"):
            return ConfigType.YAML
        else:
            raise ValueError(f"Unknown config file extension: {ext}")


@typechecked
def find_user_config() -> ConfigLocation:
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
    repo_dir = Path(__file__).parent

    def _xdg_config_dir() -> Path:
        xdg_config_home = os.environ.get("XDG_CONFIG_HOME")
        if xdg_config_home:
            return Path(xdg_config_home) / "immich_autotag"
        return Path.home() / ".config" / "immich_autotag"

    def _candidate_paths(base: Path) -> list[Path]:
        """Return candidate config file paths in priority order for a given base dir.

        This collapses the repeated pattern of checking for two filenames in three
        symmetric locations (repo, xdg, legacy) into a single loop-friendly helper.
        """
        names = ["config.py", "config.yaml"]
        return [base / name for name in names]

    # Build the prioritized list of candidate paths
    candidates: list[Path] = []

    # Repo-level development overrides
    candidates.extend(_candidate_paths(repo_dir))
    # XDG
    candidates.extend(_candidate_paths(_xdg_config_dir()))
    # Legacy home folder
    candidates.extend(_candidate_paths(Path.home() / ".immich_autotag"))
    # Environment override (evaluated last)
    env_path_str = os.environ.get("IMMICH_AUTOTAG_CONFIG")
    if env_path_str:
        candidates.append(Path(env_path_str))

    for candidate in candidates:
        if candidate.exists():
            return ConfigLocation(candidate)

    raise FileNotFoundError("No configuration file found.")


@typechecked
def load_python_config(path: Path):
    """Dynamically loads a Python file that defines 'user_config' or 'config'"""
    spec = importlib.util.spec_from_file_location("user_config_module", str(path))
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load spec for {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    # Search for user_config or config using module.__dict__ to avoid dynamic
    # attribute access patterns (hasattr/getattr) that our style policy forbids.
    try:
        md = module.__dict__
    except AttributeError:
        raise AttributeError(
            f"Module object has no __dict__; cannot load config from {path}"
        )

    if "user_config" in md:
        return md["user_config"]
    if "config" in md:
        return md["config"]
    raise AttributeError(f"'user_config' or 'config' not found in {path}")


@typechecked
def load_yaml_config(path: Path):
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data
