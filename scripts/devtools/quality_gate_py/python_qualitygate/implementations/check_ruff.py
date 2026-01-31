
import subprocess
from python_qualitygate.cli.args import QualityGateArgs
import attr
from python_qualitygate.core.base import Check
from python_qualitygate.core.result import CheckResult, Finding

@attr.define(auto_attribs=True, slots=True)
class CheckRuff(Check):
    name = 'check_ruff'

    def check(self, args: QualityGateArgs) -> CheckResult:
        from python_qualitygate.core.enums_level import QualityGateLevel
        findings = []
        cmd = [args.py_bin, '-m', 'ruff', 'check', '--fix']
        match args.level:
            case QualityGateLevel.STANDARD | QualityGateLevel.TARGET:
                cmd += ['--ignore', 'E501']
            case QualityGateLevel.STRICT:
                pass
            case _:
                raise ValueError(f"Unknown QualityGateLevel: {args.level}")
        cmd.append(str(args.target_dir))
        print(f"[RUN] {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        output = result.stdout + '\n' + result.stderr
        match args.level:
            case QualityGateLevel.STANDARD | QualityGateLevel.TARGET:
                f821_lines = [line for line in output.splitlines() if 'F821' in line]
                if f821_lines:
                    for line in f821_lines:
                        findings.append(Finding(file_path=args.target_dir, line_number=0, message=line, code="ruff-F821"))
                return CheckResult(findings=findings)
            case QualityGateLevel.STRICT:
                if result.returncode != 0:
                    for line in output.splitlines():
                        if line.strip():
                            findings.append(Finding(file_path=args.target_dir, line_number=0, message=line.strip(), code="ruff"))
                return CheckResult(findings=findings)
            case _:
                raise ValueError(f"Unknown QualityGateLevel: {args.level}")

    def apply(self, args: QualityGateArgs) -> CheckResult:
        # Same behavior as check (auto-fix is already in the command)
        return self.check(args)
