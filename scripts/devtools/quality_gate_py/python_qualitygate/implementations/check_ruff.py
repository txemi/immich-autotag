

import subprocess
from python_qualitygate.cli.args import QualityGateArgs
import attr
from python_qualitygate.core.base import Check
from python_qualitygate.core.result import CheckResult, Finding

@attr.define(auto_attribs=True, slots=True)
class CheckRuff(Check):
    name = 'check_ruff'

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

    def _process_check_output(self, args: QualityGateArgs, output: str, returncode: int) -> CheckResult:
        """Process ruff output and return findings based on quality level."""
        from python_qualitygate.core.enums_level import QualityGateLevel
        
        findings: list[Finding] = []
        
        match args.level:
            case QualityGateLevel.STANDARD | QualityGateLevel.TARGET:
                # OPTION #2 ACTIVATED: Block all ruff errors (except E501, already ignored in command)
                if returncode != 0:
                    for line in output.splitlines():
                        if line.strip() and not line.startswith('warning:'):
                            findings.append(Finding(file_path=args.target_dir, line_number=0, message=line.strip(), code="ruff"))
            case QualityGateLevel.STRICT:
                if returncode != 0:
                    for line in output.splitlines():
                        if line.strip():
                            findings.append(Finding(file_path=args.target_dir, line_number=0, message=line.strip(), code="ruff"))
            case _:
                raise ValueError(f"Unknown QualityGateLevel: {args.level}")
        
        return CheckResult(findings=findings)

    def check(self, args: QualityGateArgs) -> CheckResult:
        cmd = self._build_ruff_command(args, apply_fix=False)
        print(f"[RUN] {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        output = result.stdout + '\n' + result.stderr
        return self._process_check_output(args, output, result.returncode)

    def apply(self, args: QualityGateArgs) -> CheckResult:
        cmd = self._build_ruff_command(args, apply_fix=True)
        print(f"[RUN] {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        # output = result.stdout + '\n' + result.stderr  # Not used in CHECK mode
        findings: list[Finding] = []
        if result.returncode != 0:
            findings.append(Finding(file_path=args.target_dir, line_number=0, message="Ruff found issues during fix", code="ruff-fix"))
        return CheckResult(findings=findings)

