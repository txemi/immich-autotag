"""
manager.py

Singleton Manager for the new experimental configuration.
"""

from pathlib import Path
from typing import Any, Optional

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
        except Exception:
            from immich_autotag.logging.levels import LogLevel
            from immich_autotag.logging.utils import log

            log("[ConfigManager] Error during config load:", level=LogLevel.ERROR)
            traceback.print_exc()
            _instance = None
            _instance_created = False
            raise

    def _construction(self):
        # --- New configuration search and loading logic ---
        self._load()
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

        self._try_load_dynamic()
        from immich_autotag.logging.levels import LogLevel
        from immich_autotag.logging.utils import log

        log(f"Config loaded successfully: {type(self.config)}", level=LogLevel.INFO)

    @typechecked
    def _try_load_dynamic(self):
        config_location = find_user_config()
        from immich_autotag.logging.levels import LogLevel
        from immich_autotag.logging.utils import log

        log(f"Found config path: {config_location.path}", level=LogLevel.INFO)

        if config_location.path is None:
            from immich_autotag.utils.user_help import print_config_help

            print_config_help()
            raise FileNotFoundError(
                "No configuration found. See the configuration guide above."
            )

        config_type = config_location.get_type()
        if config_type == config_type.__class__.PYTHON:
            from immich_autotag.logging.levels import LogLevel
            from immich_autotag.logging.utils import log

            log(
                f"Loading Python config from {config_location.path}",
                level=LogLevel.INFO,
            )
            config_obj = load_python_config(config_location.path)
            if isinstance(config_obj, UserConfig):
                self.config = config_obj
            else:
                print("[CONFIG] Validating config object as UserConfig...")
                self.config = UserConfig.model_validate(config_obj)
        elif config_type == config_type.__class__.YAML:
            from immich_autotag.logging.levels import LogLevel
            from immich_autotag.logging.utils import log

            log(f"Loading YAML config from {config_location.path}", level=LogLevel.INFO)
            config_data = load_yaml_config(config_location.path)
            self.config = UserConfig.model_validate(config_data)
        else:
            from immich_autotag.utils.user_help import print_config_help

            print_config_help()
            raise FileNotFoundError(
                "No configuration found. See the configuration guide above."
            )

    @staticmethod
    @typechecked
    def get_instance() -> "ConfigManager":
        global _instance
        if _instance is None:
            ConfigManager()
        assert _instance is not None
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

        @typechecked
        def enum_representer(dumper: Any, data: "enum.Enum") -> Any:
            try:
                rep = str(data.value)
            except Exception:
                rep = str(data)
            return dumper.represent_data(rep)

        yaml.add_representer(enum.Enum, enum_representer)
        # Standard dump
        with open(str(path), "w", encoding="utf-8") as f:
            yaml.dump(self.config.model_dump(), f, allow_unicode=True, sort_keys=False)

        # Alternative dump with comments
        try:
            from immich_autotag.config.yaml_with_comments import (
                generate_yaml_with_comments,
            )

            commented_path = str(path).replace(".yaml", "_with_comments.yaml")
            generate_yaml_with_comments(type(self.config), commented_path)
        except Exception as e:
            from immich_autotag.logging.levels import LogLevel
            from immich_autotag.logging.utils import log

            log(f"Could not generate commented YAML: {e}", level=LogLevel.WARNING)

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
        if config is None:
            return False
        # Prefer explicit access to known config fields. The skip/resume logic
        # is represented in `SkipConfig.resume_previous` on `UserConfig.skip`.
        # Access fields explicitly to avoid dynamic attribute lookups (getattr).
        try:
            return bool(config.skip.resume_previous)
        except Exception:
            return False


# --- Automatic loading at startup (usage example) ---
