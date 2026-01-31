

from typing import Any
from python_qualitygate.core.result import CheckResult
from abc import ABC, abstractmethod

class Check(ABC):
    name: str = ''  # Should be overridden as a class variable in subclasses

    @abstractmethod
    def check(self, args: Any) -> CheckResult:
        ...

    @abstractmethod
    def apply(self, args: Any) -> CheckResult:
        ...
