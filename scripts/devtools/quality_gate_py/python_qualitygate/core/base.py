

from python_qualitygate.core.result import QualityGateResult
from python_qualitygate.cli.args import QualityGateArgs
from abc import ABC, abstractmethod


class Check(ABC):
    @abstractmethod
    def get_name(self) -> str:
        ...

    @abstractmethod
    def check(self, args: QualityGateArgs) -> QualityGateResult:
        ...

    @abstractmethod
    def apply(self, args: QualityGateArgs) -> QualityGateResult:
        ...
