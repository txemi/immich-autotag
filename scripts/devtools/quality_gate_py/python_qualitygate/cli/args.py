from __future__ import annotations



import attr
from pathlib import Path
from typing import Optional, TYPE_CHECKING
from python_qualitygate.core.enums_mode import QualityGateMode
from python_qualitygate.core.enums_level import QualityGateLevel

if TYPE_CHECKING:
    from python_qualitygate.core.base import Check


@attr.define(auto_attribs=True, slots=True, kw_only=True)
class QualityGateArgs:
    level: QualityGateLevel = QualityGateLevel.STANDARD
    mode: QualityGateMode = QualityGateMode.APPLY
    py_bin: str = 'python3'
    line_length: int = 88
    target_dir: Path = Path('immich_autotag')
    only_check: Optional[type["Check"]] = attr.field(default=None, validator=attr.validators.optional(attr.validators.instance_of(type)))
