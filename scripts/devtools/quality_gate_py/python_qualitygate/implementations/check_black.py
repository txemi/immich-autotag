
import subprocess
from python_qualitygate.cli.args import QualityGateArgs
import attr
from python_qualitygate.core.base import Check
from python_qualitygate.core.result import QualityGateResult, Finding

@attr.define(auto_attribs=True, slots=True)
class CheckBlack(Check):
    _name: str = attr.ib(default='check_black', init=False)

    def get_name(self) -> str:
        return self._name

    def check(self, args: QualityGateArgs) -> QualityGateResult:
        cmd = [args.py_bin, '-m', 'black', '--check', '--line-length', str(args.line_length), str(args.target_dir)]
        print(f"[RUN] {' '.join(cmd)}")
        findings = []
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            # If Black succeeds, no findings
            return QualityGateResult(findings=[])
        except subprocess.CalledProcessError as exc:
            # Black returns exit code 1 for formatting issues
            if exc.returncode == 1:
                output = exc.stdout or exc.stderr or ""
                for line in output.splitlines():
                    if line.strip().endswith('would reformat'):
                        file_path = line.split()[0]
                        findings.append(Finding(file_path=file_path, line_number=0, message="File not formatted with black", code="black-format"))
                if not findings:
                    msg = output.strip() or "Black found formatting errors"
                    findings.append(Finding(file_path=args.target_dir, line_number=0, message=msg, code="black-format"))
                return QualityGateResult(findings=findings)
            else:
                # Tool error: propagate exception to fail script
                raise

    def apply(self, args: QualityGateArgs) -> QualityGateResult:
        cmd = [args.py_bin, '-m', 'black', '--line-length', str(args.line_length), str(args.target_dir)]
        print(f"[RUN] {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        findings = []
        if result.returncode != 0:
            findings.append(Finding(file_path=args.target_dir, line_number=0, message="Black could not format all files", code="black-apply-error"))
        return QualityGateResult(findings=findings)
