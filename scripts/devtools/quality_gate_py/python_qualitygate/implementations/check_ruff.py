

import subprocess
from python_qualitygate.cli.args import QualityGateArgs
import attr
from python_qualitygate.core.base import Check
from python_qualitygate.core.result import CheckResult, Finding

@attr.define(auto_attribs=True, slots=True)
class CheckRuff(Check):
    _name: str = attr.ib(default='check_ruff', init=False)

    def get_name(self) -> str:
        return self._name

    def _build_ruff_command(self, args: QualityGateArgs, apply_fix: bool) -> list[str]:
        """Build the ruff command with appropriate flags based on level and mode."""
        from python_qualitygate.core.enums_level import QualityGateLevel
        
        cmd = [args.py_bin, '-m', 'ruff', 'check']
        
        if apply_fix:
            cmd.append('--fix')
        
        match args.level:
            case QualityGateLevel.STANDARD | QualityGateLevel.TARGET:
                cmd += ['--ignore', 'E501']
            case QualityGateLevel.STRICT:
                pass
            case _:
                raise ValueError(f"Unknown QualityGateLevel: {args.level}")
        
        cmd.append(str(args.target_dir))
        return cmd

    def _process_check_output(self, args: QualityGateArgs, output: str, returncode: int, code: str = "ruff") -> CheckResult:
        """Process ruff output and return findings based on quality level. Parametrizable code."""
        from python_qualitygate.core.enums_level import QualityGateLevel

        findings: list[Finding] = []

        match args.level:
            case QualityGateLevel.STANDARD | QualityGateLevel.TARGET:
                if returncode != 0:
                    for line in output.splitlines():
                        if line.strip() and not line.startswith('warning:'):
                            findings.append(Finding(file_path=args.target_dir, line_number=0, message=line.strip(), code=code))
            case QualityGateLevel.STRICT:
                if returncode != 0:
                    for line in output.splitlines():
                        if line.strip():
                            findings.append(Finding(file_path=args.target_dir, line_number=0, message=line.strip(), code=code))
            case _:
                raise ValueError(f"Unknown QualityGateLevel: {args.level}")

        return CheckResult(findings=findings)

    def _run_ruff(self, args: QualityGateArgs, apply_fix: bool, code: str) -> CheckResult:
        # The 'code' argument is used to label the origin of the finding in the results:
        #   - "ruff" for checks (check),
        #   - "ruff-fix" for automatic fixes (apply/fix).
        # This allows reports to distinguish whether a finding comes from a check or from applying fixes.
        cmd = self._build_ruff_command(args, apply_fix=apply_fix)
        print(f"[RUN] {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        output = result.stdout + '\n' + result.stderr
        return self._process_check_output(args, output, result.returncode, code=code)

    def check(self, args: QualityGateArgs) -> CheckResult:
        return self._run_ruff(args, apply_fix=False, code="ruff")

    def apply(self, args: QualityGateArgs) -> CheckResult:
        return self._run_ruff(args, apply_fix=True, code="ruff-fix")

