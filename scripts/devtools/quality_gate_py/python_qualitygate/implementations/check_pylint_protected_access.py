import subprocess
import attr
from python_qualitygate.core.base import Check
from python_qualitygate.core.result import CheckResult, Finding
from python_qualitygate.cli.args import QualityGateArgs


@attr.define(auto_attribs=True, slots=True)
class CheckPylintProtectedAccess(Check):
    _name: str = attr.ib(default='check_pylint_protected_access', init=False)

    def get_name(self) -> str:
        return self._name

    def check(self, args: QualityGateArgs) -> CheckResult:
        cmd = [args.py_bin, '-m', 'pylint', '--disable=all', '--enable=protected-access', str(args.target_dir)]
        result = subprocess.run(cmd, capture_output=True, text=True)
        findings = []
        if result.returncode != 0:
            for line in result.stdout.splitlines():
                if "W0212" in line:
                    findings.append(Finding(
                        file_path="pylint",
                        line_number=0,
                        message=line.strip(),
                        code="protected-access"
                    ))
        return CheckResult(findings=findings)

    def apply(self, args: QualityGateArgs) -> CheckResult:
        return self.check(args)
