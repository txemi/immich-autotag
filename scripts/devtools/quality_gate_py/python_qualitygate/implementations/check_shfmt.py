
import attr
from python_qualitygate.cli.args import QualityGateArgs
from python_qualitygate.core.base import Check
from python_qualitygate.core.result import QualityGateResult, Finding
from scripts.devtools.quality_gate_py.python_qualitygate.implementations.common_qualitygate import run_subprocess_and_process

@attr.define(auto_attribs=True, slots=True)
class CheckShfmt(Check):
    _name: str = attr.ib(default='check_shfmt', init=False)

    def get_name(self) -> str:
        return self._name

    def check(self, args: QualityGateArgs) -> QualityGateResult:
        cmd = ['shfmt', '-d', '-i', '0', 'scripts/']
        from pathlib import Path
        def process_line(line):
            if line.strip():
                return Finding(file_path=Path('scripts/'), line_number=0, message=line.strip(), code="shfmt")
            return None
        return run_subprocess_and_process(cmd, process_line, error_code=1, target_dir='scripts/', code="shfmt")

    def apply(self, args: QualityGateArgs) -> QualityGateResult:
        cmd = ['shfmt', '-w', '-i', '0', 'scripts/']
        from pathlib import Path
        def process_line(line):
            if line.strip():
                return Finding(file_path=Path('scripts/'), line_number=0, message=line.strip(), code="shfmt")
            return None
        return run_subprocess_and_process(cmd, process_line, error_code=1, target_dir='scripts/', code="shfmt")
