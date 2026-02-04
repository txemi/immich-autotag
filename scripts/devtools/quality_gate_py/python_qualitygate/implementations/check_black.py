
import subprocess
from python_qualitygate.cli.args import QualityGateArgs
import attr
from python_qualitygate.core.base import Check
from python_qualitygate.core.result import CheckResult, Finding

@attr.define(auto_attribs=True, slots=True)
class CheckBlack(Check):
    _name: str = attr.ib(default='check_black', init=False)

    def get_name(self) -> str:
        return self._name

    def check(self, args: QualityGateArgs) -> CheckResult:
        cmd = [args.py_bin, '-m', 'black', '--check', '--line-length', str(args.line_length), str(args.target_dir)]
        print(f"[RUN] {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        findings = []
        if result.returncode != 0:
            # Parse affected files from black's output
            for line in result.stdout.splitlines():
                if line.strip().endswith('would reformat'):
                    file_path = line.split()[0]
                    findings.append(Finding(file_path=file_path, line_number=0, message="File not formatted with black", code="black-format"))
            if not findings:
                # If no specific files, include the full Black output for context
                msg = result.stdout.strip() or "Black found formatting errors"
                findings.append(Finding(file_path=args.target_dir, line_number=0, message=msg, code="black-format"))
        return CheckResult(findings=findings)

    def apply(self, args: QualityGateArgs) -> CheckResult:
        cmd = [args.py_bin, '-m', 'black', '--line-length', str(args.line_length), str(args.target_dir)]
        print(f"[RUN] {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        findings = []
        if result.returncode != 0:
            findings.append(Finding(file_path=args.target_dir, line_number=0, message="Black could not format all files", code="black-apply-error"))
        return CheckResult(findings=findings)
