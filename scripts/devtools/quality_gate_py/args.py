from dataclasses import dataclass
from scripts.devtools.quality_gate_py.enums_mode import QualityGateMode
from scripts.devtools.quality_gate_py.enums_level import QualityGateLevel

@dataclass
class QualityGateArgs:
    level: QualityGateLevel = QualityGateLevel.STANDARD
    mode: QualityGateMode = QualityGateMode.APPLY
    py_bin: str = 'python3'
    max_line_length: int = 88
    target_dir: str = 'immich_autotag'
    only_check: str = ''
