"""
manager.py

Singleton Manager for the new experimental configuration.
"""

from pathlib import Path
from typeguard import typechecked
import yaml
import attrs
from typing import Optional
from .models import UserConfig

_instance = None
_instance_created = False


@attrs.define(auto_attribs=True, slots=True, kw_only=True)
class ExperimentalConfigManager:

    config: Optional[UserConfig] = None

    def __attrs_post_init__(self):
        global _instance, _instance_created
        if _instance_created:
            raise RuntimeError(
                "ExperimentalConfigManager instance already exists. Use get_instance()."
            )
        _instance_created = True
        _instance = self

    @staticmethod
    @typechecked
    def get_instance() -> "ExperimentalConfigManager":
        global _instance
        if _instance is None:
            ExperimentalConfigManager()
        return _instance

    @typechecked
    def load_config(self, config_path: Path):
        with open(config_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        self.config = UserConfig.model_validate(data)

    @typechecked
    def load_config_from_real_python(self):
        """
        Loads the configuration by directly importing user_real_config from user_real_config_pydantic.py.
        Does not use importlib or dynamic logic, only explicit import.
        """
        from .user_real_config_pydantic import user_real_config

        self.config = user_real_config

    @typechecked
    def dump_to_yaml(self, path: str = None):
        """Dumps the current configuration to a YAML file in the default logs/output folder."""
        if self.config is None:
            raise RuntimeError("No configuration loaded to dump to YAML.")
        import yaml
        from immich_autotag.utils.run_output_dir import get_run_output_dir
        if path is None:
            out_dir = get_run_output_dir()
            path = out_dir / "user_config_dump.yaml"
        with open(path, "w", encoding="utf-8") as f:
            yaml.safe_dump(
                self.config.model_dump(), f, allow_unicode=True, sort_keys=False
            )

    def print_config(self):
        """Prints the current configuration to screen in a readable format."""
        if self.config is None:
            print("[WARN] No configuration loaded.")
            return
        import pprint

        pprint.pprint(self.config.model_dump())


# --- Carga automática al inicio (ejemplo de uso) ---


@typechecked
def load_experimental_config_at_startup():
    config_path = Path(__file__).parent / "user_real_config.yaml"
    # If the file does not exist, raise a clear error
    if not config_path.exists():
        raise FileNotFoundError(
            f"Experimental configuration template not found at: {config_path}"
        )
    # Only create the singleton if it does not exist
    manager = ExperimentalConfigManager.get_instance()
    manager.load_config_from_real_python()
    # Print the loaded configuration to see the result
    import pprint

    pprint.pprint(manager.config.model_dump() if manager.config else None)
