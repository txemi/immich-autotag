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
            raise RuntimeError("ExperimentalConfigManager instance already exists. Use get_instance().")
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
        Carga la configuración importando directamente user_real_config de user_real_config_pydantic.py.
        No usa importlib ni lógica dinámica, solo import explícito.
        """
        from .user_real_config_pydantic import user_real_config
        self.config = user_real_config     

    @typechecked           
    def dump_to_yaml(self, path: str = "user_config_dump.yaml"):
        """Vuelca la configuración actual a un fichero YAML."""
        if self.config is None:
            raise RuntimeError("No hay configuración cargada para volcar a YAML.")
        import yaml
        with open(path, "w", encoding="utf-8") as f:
            yaml.safe_dump(self.config.model_dump(), f, allow_unicode=True, sort_keys=False)

    def print_config(self):
        """Imprime la configuración actual por pantalla de forma legible."""
        if self.config is None:
            print("[WARN] No hay configuración cargada.")
            return
        import pprint
        pprint.pprint(self.config.model_dump())

# --- Carga automática al inicio (ejemplo de uso) ---

@typechecked
def load_experimental_config_at_startup():
    config_path = Path(__file__).parent / "user_real_config.yaml"
    # Si el archivo no existe, lanza un error claro
    if not config_path.exists():
        raise FileNotFoundError(f"No se encontró la plantilla de configuración experimental en: {config_path}")
    # Solo crear el singleton si no existe
    manager = ExperimentalConfigManager.get_instance()
    manager.load_config_from_real_python()
    # Imprimir la configuración cargada para ver el resultado
    import pprint
    pprint.pprint(manager.config.model_dump() if manager.config else None)
