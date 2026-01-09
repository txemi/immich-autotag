# To load the checkpoint, import from immich_autotag.duplicates.checkpoint_loader
"""
manager.py

Singleton Manager for the new experimental configuration.
"""

from pathlib import Path
from typing import Optional

import attrs
import yaml
from typeguard import typechecked


from .models import UserConfig
from .config_finder import find_user_config, load_python_config, load_yaml_config

_instance = None
_instance_created = False


@attrs.define(auto_attribs=True, slots=True, kw_only=True)
class ConfigManager:

    config: Optional[UserConfig] = None

    def __attrs_post_init__(self):
        global _instance, _instance_created
        if _instance_created:
            raise RuntimeError(
                "ConfigManager instance already exists. Use get_instance()."
            )
        _instance_created = True
        _instance = self
        # --- New configuration search and loading logic ---
        config_type, config_path = find_user_config()
        if config_type == "python":
            config_obj = load_python_config(config_path)
            if isinstance(config_obj, UserConfig):
                self.config = config_obj
            else:
                # Intentar validar si es un dict
                self.config = UserConfig.model_validate(config_obj)
        elif config_type == "yaml":
            config_data = load_yaml_config(config_path)
            self.config = UserConfig.model_validate(config_data)
        else:
            from immich_autotag.utils.user_help import print_config_help
            print_config_help()
            raise FileNotFoundError(
                "No configuration found. See the configuration guide above."
            )
        # Initialize skip_n with the counter from the last previous execution (with overlap)
        try:
            from immich_autotag.statistics.statistics_checkpoint import (
                get_previous_skip_n,
            )
            prev_skip_n = get_previous_skip_n()
            if prev_skip_n is not None and hasattr(self.config, "skip_n"):
                self.config.skip_n = prev_skip_n
        except Exception as e:
            print(
                f"[WARN] Could not initialize skip_n from previous statistics: {e}"
            )
        self.print_config()

    @staticmethod
    @typechecked
    def get_instance() -> "ConfigManager":
        global _instance
        if _instance is None:
            ConfigManager()
        return _instance

    @typechecked
    def load_config(self, config_path: Path):
        with open(config_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        self.config = UserConfig.model_validate(data)
        # Save a record of the loaded config to logs/output
        self.dump_to_yaml()

    @typechecked
    def load_config_from_real_python(self):
        """
        (Legacy) Loads the configuration by directly importing user_config from user_config.py (development mode only).
        """
        from .user_config import user_config
        self.config = user_config
        self.dump_to_yaml()

    @typechecked
    def dump_to_yaml(self, path: "str | Path | None" = None):
        """Dumps the current configuration to a YAML file in the default logs/output folder."""
        if self.config is None:
            raise RuntimeError("No configuration loaded to dump to YAML.")
        from pathlib import Path as _Path

        import yaml

        from immich_autotag.utils.run_output_dir import get_run_output_dir

        if path is None:
            out_dir = get_run_output_dir()
            path = out_dir / "user_config_dump.yaml"
        if not isinstance(path, (str, _Path)):
            raise TypeError(f"path must be str, Path or None, got {type(path)}")
        with open(str(path), "w", encoding="utf-8") as f:
            yaml.safe_dump(
                self.config.model_dump(), f, allow_unicode=True, sort_keys=False
            )

    @typechecked
    def print_config(self):
        """Prints the current configuration using the logging system (FOCUS level)."""
        from immich_autotag.logging.levels import LogLevel
        from immich_autotag.logging.utils import log

        if self.config is None:
            log("[WARN] No configuration loaded.", level=LogLevel.FOCUS)
            raise RuntimeError("No configuration loaded to print.")
        import pprint

        config_str = pprint.pformat(self.config.model_dump())
        log(f"Loaded config:\n{config_str}", level=LogLevel.FOCUS)


# --- Automatic loading at startup (usage example) ---


@typechecked
def load_config_at_startup():
    config_path = Path(__file__).parent / "user_config.yaml"
    # If the file does not exist, raise a clear error
    if not config_path.exists():
        raise FileNotFoundError(
            f"Experimental configuration template not found at: {config_path}"
        )
    # Only create the singleton if it does not exist
    manager = ConfigManager.get_instance()
    manager.load_config_from_real_python()
    # Print the loaded configuration to see the result
    import pprint

    pprint.pprint(manager.config.model_dump() if manager.config else None)
