
# Para cargar el checkpoint, importar desde immich_autotag.duplicates.checkpoint_loader
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
        # Cargar la configuración automáticamente al crear el singleton
        self.load_config_from_real_python()
        # Inicializar skip_n con el contador de la última ejecución previa (con solapamiento)
        try:
            from immich_autotag.statistics.statistics_checkpoint import get_previous_skip_n
            prev_skip_n = get_previous_skip_n()
            if prev_skip_n is not None and hasattr(self.config, 'skip_n'):
                self.config.skip_n = prev_skip_n
        except Exception as e:
            print(f"[WARN] No se pudo inicializar skip_n desde la estadística previa: {e}")
        self.print_config()

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
        # Save a record of the loaded config to logs/output
        self.dump_to_yaml()

    @typechecked
    def load_config_from_real_python(self):
        """
        Loads the configuration by directly importing user_real_config from user_real_config_pydantic.py.
        Does not use importlib or dynamic logic, only explicit import.
        """
        from .user_real_config_pydantic import user_real_config

        self.config = user_real_config
        # Save a record of the loaded config to logs/output
        self.dump_to_yaml()

    @typechecked
    def dump_to_yaml(self, path: "str | Path | None" = None):
        """Vuelca la configuración actual a un fichero YAML en la carpeta de logs/salida por defecto."""
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
        """Imprime la configuración actual usando el sistema de logs (nivel FOCUS)."""
        from immich_autotag.logging.levels import LogLevel
        from immich_autotag.logging.utils import log

        if self.config is None:
            log("[WARN] No configuration loaded.", level=LogLevel.FOCUS)
            raise RuntimeError("No hay configuración cargada para imprimir.")
        import pprint

        config_str = pprint.pformat(self.config.model_dump())
        log(f"Loaded config:\n{config_str}", level=LogLevel.FOCUS)


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
