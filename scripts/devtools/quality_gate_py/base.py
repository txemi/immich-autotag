from abc import ABC, abstractmethod
from typing import Any

class Check(ABC):
    """Interfaz base para todos los checks."""
    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def check(self, args: Any) -> int:
        """Modo solo comprobación (no modifica nada). Devuelve 0 si OK, !=0 si error."""
        pass

    @abstractmethod
    def apply(self, args: Any) -> int:
        """Modo aplicar (puede modificar ficheros). Devuelve 0 si OK, !=0 si error."""
        pass
