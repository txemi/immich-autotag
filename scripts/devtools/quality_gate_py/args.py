from dataclasses import dataclass

@dataclass
class QualityGateArgs:
    level: str = 'STANDARD'
    mode: str = 'APPLY'
    py_bin: str = 'python3'
    max_line_length: int = 88
    target_dir: str = 'immich_autotag'
    only_check: str = ''
