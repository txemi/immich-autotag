"""
manager.py

Gestor Singleton para la nueva configuración experimental.
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
        # Cargar la configuración automáticamente al crear el singleton
        self.load_config_from_real_python()
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
        Carga la configuración importando directamente user_real_config de user_real_config_pydantic.py.
        No usa importlib ni lógica dinámica, solo import explícito.
        """
        from .user_real_config_pydantic import user_real_config

        self.config = user_real_config
        # Save a record of the loaded config to logs/output
        self.dump_to_yaml()

    @typechecked
    def dump_to_yaml(self, path: 'str | Path | None' = None):
        """Vuelca la configuración actual a un fichero YAML en la carpeta de logs/salida por defecto."""
        if self.config is None:
            raise RuntimeError("No hay configuración cargada para volcar a YAML.")
        import yaml
        from pathlib import Path as _Path
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
        from immich_autotag.logging.utils import log
        from immich_autotag.logging.levels import LogLevel
        if self.config is None:
            log("[WARN] No configuration loaded.", level=LogLevel.FOCUS)
            raise RuntimeError("No hay configuración cargada para imprimir.")   
        import pprint
        config_str = pprint.pformat(self.config.model_dump())
        log(f"Loaded config:\n{config_str}", level=LogLevel.FOCUS)
    @typechecked
    def is_classification_tag(self, tag: str) -> bool:
        """Devuelve True si el tag es clasificador según la configuración cargada."""
        if not self.config or not hasattr(self.config, 'classification_tags'):
            raise RuntimeError("No hay configuración o no se encuentra classification_tags en la config.")
        return any(tag.lower() == t.lower() for t in self.config.classification_tags)

# --- Carga automática al inicio (ejemplo de uso) ---


@typechecked
def load_experimental_config_at_startup():
    config_path = Path(__file__).parent / "user_real_config.yaml"
    # Si el archivo no existe, lanza un error claro
    if not config_path.exists():
        raise FileNotFoundError(
            f"No se encontró la plantilla de configuración experimental en: {config_path}"
        )
    # Solo crear el singleton si no existe
    manager = ExperimentalConfigManager.get_instance()
    manager.load_config_from_real_python()
    # Imprimir la configuración cargada para ver el resultado
    import pprint

    pprint.pprint(manager.config.model_dump() if manager.config else None)
