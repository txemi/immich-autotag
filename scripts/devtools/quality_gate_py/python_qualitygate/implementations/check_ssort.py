
import subprocess
from python_qualitygate.cli.args import QualityGateArgs
import attr
from python_qualitygate.core.base import Check
from python_qualitygate.core.result import CheckResult, Finding

@attr.define(auto_attribs=True, slots=True)
class CheckSsort(Check):
    name = 'check_ssort'

    def check(self, args: QualityGateArgs) -> CheckResult:
        cmd = ['ssort', '--check', args.target_dir]
        print(f"[RUN] {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        findings = []
        if result.returncode != 0:
            for line in result.stdout.splitlines():
                if line.strip():
                    findings.append(Finding(file_path=args.target_dir, line_number=0, message=line.strip(), code="ssort"))
        return CheckResult(findings=findings)

    def apply(self, args: QualityGateArgs) -> CheckResult:
        cmd = ['ssort', args.target_dir]
        print(f"[RUN] {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        findings = []
        if result.returncode != 0:
            for line in result.stdout.splitlines():
                if line.strip():
                    findings.append(Finding(file_path=args.target_dir, line_number=0, message=line.strip(), code="ssort"))
        return CheckResult(findings=findings)
