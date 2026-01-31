
import subprocess
from python_qualitygate.cli.args import QualityGateArgs
import attr
from python_qualitygate.core.base import Check
from python_qualitygate.core.result import CheckResult, Finding

@attr.define(auto_attribs=True, slots=True)
class CheckIsort(Check):
    name = 'check_isort'

    def check(self, args: QualityGateArgs) -> CheckResult:
        cmd = [args.py_bin, '-m', 'isort', '--profile', 'black', '--check-only', '--line-length', str(args.line_length), str(args.target_dir)]
        print(f"[RUN] {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        findings = []
        if result.returncode != 0:
            for line in result.stdout.splitlines():
                # isort output: path:line:col: message (sometimes just file path)
                if line.strip():
                    findings.append(Finding(file_path=args.target_dir, line_number=0, message=line.strip(), code="isort"))
        return CheckResult(findings=findings)

    def apply(self, args: QualityGateArgs) -> CheckResult:
        cmd = [args.py_bin, '-m', 'isort', '--profile', 'black', '--line-length', str(args.line_length), str(args.target_dir)]
        print(f"[RUN] {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        findings = []
        # isort apply should not fail, but capture output just in case
        if result.returncode != 0:
            for line in result.stdout.splitlines():
                if line.strip():
                    findings.append(Finding(file_path=args.target_dir, line_number=0, message=line.strip(), code="isort"))
        return CheckResult(findings=findings)
