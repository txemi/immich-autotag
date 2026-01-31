from typing import List, Any
from pathlib import Path
import attr

@attr.define(auto_attribs=True, slots=True)
class Finding:
    file_path: Path
    line_number: int
    message: str
    code: str = ''  # opcional, para tipo de warning/error

@attr.define(auto_attribs=True, slots=True)
class CheckResult:
    findings: List[Finding]
    # Puedes añadir más campos si quieres (por ejemplo, success, summary, etc)

    def is_success(self) -> bool:
        return len(self.findings) == 0
