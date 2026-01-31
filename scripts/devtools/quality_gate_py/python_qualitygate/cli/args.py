from dataclasses import dataclass
from python_qualitygate.core.enums_mode import QualityGateMode
from python_qualitygate.core.enums_level import QualityGateLevel

@dataclass(slots=True, frozen=True)
class QualityGateArgs:
    level: QualityGateLevel = QualityGateLevel.STANDARD
    mode: QualityGateMode = QualityGateMode.APPLY
    py_bin: str = 'python3'
    max_line_length: int = 88
    target_dir: str = 'immich_autotag'
    only_check: str = ''
