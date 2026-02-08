
import subprocess
from python_qualitygate.cli.args import QualityGateArgs
import attr
from python_qualitygate.core.base import Check
from python_qualitygate.core.result import QualityGateResult, Finding
from python_qualitygate.core.result import QualityGateResult, Finding
@attr.define(auto_attribs=True, slots=True)
class CheckNoTuples(Check):
    _name: str = attr.ib(default='check_no_tuples', init=False)

    def get_name(self) -> str:
        return self._name

    def check(self, args: QualityGateArgs) -> QualityGateResult:
        from pathlib import Path
        import sys
        sys.path.append(str(Path('scripts/devtools')))
        from check_no_tuples import run_check_no_tuples
        from check_no_tuples_types import NoTuplesFinding
        excludes = {'.venv', 'immich-client', 'scripts'}
        findings_raw = run_check_no_tuples(Path(args.target_dir), excludes)
        findings = [
            Finding(
                file_path=f.file,
                line_number=f.line,
                message=f.message,
                code="no_tuples"
            ) for f in findings_raw
        ]
        return QualityGateResult(findings=findings)
    def apply(self, args: QualityGateArgs) -> QualityGateResult:
        # Este check solo checkea, no modifica
        return self.check(args)
        return self.check(args)
