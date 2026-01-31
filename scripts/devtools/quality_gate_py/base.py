from abc import ABC, abstractmethod
from typing import Any

class Check(ABC):
    """Base interface for all checks."""
    def __init__(self, name: str):
        self.name = name


    @abstractmethod
    def check(self, args: Any) -> int:
        """Check-only mode (does not modify anything). Returns 0 if OK, !=0 if error."""
        pass

    @abstractmethod
    def apply(self, args: Any) -> int:
        """Apply mode (may modify files). Returns 0 if OK, !=0 if error."""
        pass
