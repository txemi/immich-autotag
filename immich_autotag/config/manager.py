"""
manager.py

Singleton Manager for the new experimental configuration.
"""

from pathlib import Path
from typing import Optional

import attrs
import yaml
from typeguard import typechecked

from .config_finder import find_user_config, load_python_config, load_yaml_config
from .models import UserConfig

_instance = None
_instance_created = False


@attrs.define(auto_attribs=True, slots=True, kw_only=True)
class ConfigManager:

    config: Optional[UserConfig] = None

    def __attrs_post_init__(self):
        import traceback

        global _instance, _instance_created
        if _instance_created:
            raise RuntimeError(
                "ConfigManager instance already exists. Use get_instance()."
            )
        try:
            # --- New configuration search and loading logic ---
            self._construction()
            # Initialize skip_n with the counter from the last previous execution (with overlap)

            _instance_created = True
            _instance = self
        except Exception as e:
            print("[ConfigManager] Error during config load:")
            traceback.print_exc()
            _instance = None
            _instance_created = False
            raise

    def _construction(self):
        # --- New configuration search and loading logic ---

        self._load()

        # Initialize skip_n with the counter from the last previous execution (with overlap)
        self._initialize_skip_n_from_checkpoint()

        # Dump the loaded configuration to the logs/output folder
        self.dump_to_yaml()
        self.print_config()

    @typechecked
    def _load(self):
        try:
            self.load_config_from_real_python()
            if self.config:
                return
        except Exception:
            pass  # Ignore and try dynamic loading

        try:
            self._try_load_dynamic()
            print(f"[CONFIG] ✅ Config loaded successfully: {type(self.config)}")
        except Exception as e:
            print(f"[CONFIG] ❌ ERROR loading config: {e}")
            print(f"[CONFIG] Exception type: {type(e).__name__}")
            import traceback

            traceback.print_exc()
            raise

    @typechecked
    def _try_load_dynamic(self):
        config_location = find_user_config()
        print(f"[CONFIG] Found config path: {config_location.path}")

        if config_location.path is None:
            from immich_autotag.utils.user_help import print_config_help

            print_config_help()
            raise FileNotFoundError(
                "No configuration found. See the configuration guide above."
            )

        config_type = config_location.get_type()
        if config_type == config_type.__class__.PYTHON:
            print(f"[CONFIG] Loading Python config from {config_location.path}")
            config_obj = load_python_config(config_location.path)
            if isinstance(config_obj, UserConfig):
                self.config = config_obj
            else:
                print(f"[CONFIG] Validating config object as UserConfig...")
                self.config = UserConfig.model_validate(config_obj)
        elif config_type == config_type.__class__.YAML:
            print(f"[CONFIG] Loading YAML config from {config_location.path}")
            config_data = load_yaml_config(config_location.path)
            self.config = UserConfig.model_validate(config_data)
        else:
            from immich_autotag.utils.user_help import print_config_help

            print_config_help()
            raise FileNotFoundError(
                "No configuration found. See the configuration guide above."
            )

    @typechecked
    def _initialize_skip_n_from_checkpoint(self):
        """
        Try to initialize skip_n from previous statistics checkpoint.
        """
        from immich_autotag.statistics.statistics_checkpoint import (
            get_previous_skip_n,
        )

        prev_skip_n = get_previous_skip_n()
        if prev_skip_n is not None:
            self.config.skip.skip_n = prev_skip_n

    @staticmethod
    @typechecked
    def get_instance() -> "ConfigManager":
        global _instance
        if _instance is None:
            ConfigManager()
            # _instance._construction()
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
        import enum

        def enum_representer(dumper, data):
            return dumper.represent_data(
                str(data.value) if hasattr(data, "value") else str(data)
            )

        yaml.add_representer(enum.Enum, enum_representer)
        with open(str(path), "w", encoding="utf-8") as f:
            yaml.dump(self.config.model_dump(), f, allow_unicode=True, sort_keys=False)

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

    @staticmethod
    def is_checkpoint_resume_enabled() -> bool:
        config = ConfigManager.get_instance().config
        try:
            return bool(config.features.enable_checkpoint_resume)
        except Exception:
            return False


# --- Automatic loading at startup (usage example) ---
