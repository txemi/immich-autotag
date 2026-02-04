
import subprocess
from python_qualitygate.cli.args import QualityGateArgs
import attr
from python_qualitygate.core.base import Check
from python_qualitygate.core.result import CheckResult, Finding

@attr.define(auto_attribs=True, slots=True)
class CheckShfmt(Check):
    _name: str = attr.ib(default='check_shfmt', init=False)

    def get_name(self) -> str:
        return self._name

    def check(self, args: QualityGateArgs) -> CheckResult:
        cmd = ['shfmt', '-d', '-i', '0']
        print(f"[RUN] {' '.join(cmd)} scripts/")
        result = subprocess.run(cmd + ['scripts/'], capture_output=True, text=True, check=True)
        from pathlib import Path
        from typing import List
        findings: List[Finding] = []
        if result.returncode != 0:
            for line in result.stdout.splitlines():
                if line.strip():
                    findings.append(Finding(file_path=Path('scripts/'), line_number=0, message=line.strip(), code="shfmt"))
        return CheckResult(findings=findings)

    def apply(self, args: QualityGateArgs) -> CheckResult:
        cmd = ['shfmt', '-w', '-i', '0']
        print(f"[RUN] {' '.join(cmd)} scripts/")
        result = subprocess.run(cmd + ['scripts/'], capture_output=True, text=True, check=True)
        from pathlib import Path
        from typing import List
        findings: List[Finding] = []
        if result.returncode != 0:
            for line in result.stdout.splitlines():
                if line.strip():
                    findings.append(Finding(file_path=Path('scripts/'), line_number=0, message=line.strip(), code="shfmt"))
        return CheckResult(findings=findings)
