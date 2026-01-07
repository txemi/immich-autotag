"""
manager.py

Gestor Singleton para la nueva configuración experimental.
"""
from pathlib import Path
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
            raise RuntimeError("ExperimentalConfigManager instance already exists. Use get_instance().")
        _instance_created = True
        _instance = self

    @staticmethod
    def get_instance() -> "ExperimentalConfigManager":
        global _instance
        if _instance is None:
            ExperimentalConfigManager()
        return _instance

    def load_config(self, config_path: Path):
        with open(config_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        self.config = UserConfig.model_validate(data)

# --- Carga automática al inicio (ejemplo de uso) ---
def load_experimental_config_at_startup():
    config_path = Path(__file__).parent / "user_config_template.yaml"
    # Si el archivo no existe, lanza un error claro
    if not config_path.exists():
        raise FileNotFoundError(f"No se encontró la plantilla de configuración experimental en: {config_path}")
    ExperimentalConfigManager()
    ExperimentalConfigManager.get_instance().load_config(config_path)
    ExperimentalConfigManager(config_path)
