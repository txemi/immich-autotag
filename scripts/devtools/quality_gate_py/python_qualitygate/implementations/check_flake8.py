
import subprocess
from python_qualitygate.cli.args import QualityGateArgs
import attr
from python_qualitygate.core.base import Check
from python_qualitygate.core.result import CheckResult, Finding

@attr.define(auto_attribs=True, slots=True)
class CheckFlake8(Check):
    name = 'check_flake8'

    def check(self, args: QualityGateArgs) -> CheckResult:
        from python_qualitygate.core.enums_level import QualityGateLevel
        from pathlib import Path
        findings = []
        base_ignore = ['E203', 'W503']
        match args.level:
            case QualityGateLevel.STRICT:
                flake8_ignore = base_ignore
            case QualityGateLevel.STANDARD | QualityGateLevel.TARGET:
                flake8_ignore = base_ignore + ['E501']
            case _:
                raise ValueError(f"Unknown QualityGateLevel: {args.level}")
        cmd = [args.py_bin, '-m', 'flake8', '--max-line-length', str(args.line_length), '--extend-ignore', ','.join(flake8_ignore), '--exclude', '.venv,immich-client,scripts,jenkins_logs', str(args.target_dir)]
        print(f"[RUN] {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            for line in result.stdout.splitlines():
                parts = line.split(':', 3)
                if len(parts) == 4:
                    file_path, line_num, col, rest = parts
                    code_msg = rest.strip().split(' ', 1)
                    code = code_msg[0] if code_msg else ''
                    msg = code_msg[1] if len(code_msg) > 1 else ''
                    findings.append(Finding(file_path=Path(file_path), line_number=int(line_num), message=msg, code=code))
                else:
                    findings.append(Finding(file_path=Path(args.target_dir), line_number=0, message=line.strip(), code="flake8-parse"))
        # Solo bloquea en STRICT
        match args.level:
            case QualityGateLevel.STRICT:
                return CheckResult(findings=findings)
            case QualityGateLevel.STANDARD | QualityGateLevel.TARGET:
                # Only warning, never blocks
                return CheckResult(findings=[])
            case _:
                raise ValueError(f"Unknown QualityGateLevel: {args.level}")

    def apply(self, args: QualityGateArgs) -> CheckResult:
        # Flake8 no modifica archivos, solo check
        return self.check(args)
