
import subprocess
from python_qualitygate.cli.args import QualityGateArgs
import attr
from python_qualitygate.core.base import Check
from python_qualitygate.core.result import CheckResult, Finding

@attr.define(auto_attribs=True, slots=True)
class CheckFlake8(Check):
    name = 'check_flake8'

    def check(self, args: QualityGateArgs) -> CheckResult:
        cmd = [args.py_bin, '-m', 'flake8', '--max-line-length', str(args.line_length), '--exclude', '.venv,immich-client,scripts,jenkins_logs', str(args.target_dir)]
        if args.level in ('STANDARD', 'TARGET'):
            cmd += ['--extend-ignore', 'E501']
        print(f"[RUN] {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        from pathlib import Path
        findings = []
        if result.returncode != 0:
            for line in result.stdout.splitlines():
                # Formato: path:line:col: code message
                parts = line.split(':', 3)
                if len(parts) == 4:
                    file_path, line_num, col, rest = parts
                    code_msg = rest.strip().split(' ', 1)
                    code = code_msg[0] if code_msg else ''
                    msg = code_msg[1] if len(code_msg) > 1 else ''
                    findings.append(Finding(file_path=Path(file_path), line_number=int(line_num), message=msg, code=code))
                else:
                    findings.append(Finding(file_path=Path(args.target_dir), line_number=0, message=line.strip(), code="flake8-parse"))
        return CheckResult(findings=findings)

    def apply(self, args: QualityGateArgs) -> CheckResult:
        # Flake8 no modifica archivos, solo check
        return self.check(args)
