


import subprocess
from python_qualitygate.cli.args import QualityGateArgs
import attr
from python_qualitygate.core.base import Check
from python_qualitygate.core.result import QualityGateResult, Finding
def _is_fatal_ruff_error(stderr: str, stdout: str) -> bool:
    """
    Returns True if the output indicates a fatal error (not just lint errors).
    Checks for common fatal error patterns.
    """
    error_text = (stderr or "") + (stdout or "")
    fatal_patterns = [
        "No module named",
        "not found",
        "Permission denied",
        "Traceback (most recent call last)",
        "ModuleNotFoundError",
        "ImportError",
        "SyntaxError",
        "command not found",
        "is not recognized as an internal or external command",
        "Error: ",
    ]
    for pat in fatal_patterns:
        if pat in error_text:
            return True
    # If both are empty, treat as fatal
    if not error_text.strip():
        return True
    return False
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

    def _process_check_output(self, args: QualityGateArgs, output: str, returncode: int, code: str = "ruff") -> QualityGateResult:
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

        return QualityGateResult(findings=findings)

    def _run_ruff(self, args: QualityGateArgs, apply_fix: bool, code: str) -> QualityGateResult:
        # The 'code' argument is used to label the origin of the finding in the results:
        #   - "ruff" for checks (check),
        #   - "ruff-fix" for automatic fixes (apply/fix).
        # This allows reports to distinguish whether a finding comes from a check or from applying fixes.
        cmd = self._build_ruff_command(args, apply_fix=apply_fix)
        print(f"[RUN] {' '.join(cmd)}")
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            output = result.stdout + '\n' + result.stderr
            return self._process_check_output(args, output, result.returncode, code=code)
        except subprocess.CalledProcessError as exc:
            output = (exc.stdout or "") + '\n' + (exc.stderr or "")
            if _is_fatal_ruff_error(exc.stderr, exc.stdout):
                # Report fatal error as finding, do not propagate
                findings = []
                error_msg = f"Ruff fatal error (exit code {exc.returncode}): {exc}"
                findings.append(Finding(file_path=args.target_dir, line_number=0, message=error_msg, code="ruff-fatal-error"))
                # Also parse stderr for details
                if exc.stderr:
                    for line in exc.stderr.splitlines():
                        if line.strip():
                            findings.append(Finding(file_path=args.target_dir, line_number=0, message=line.strip(), code="ruff-fatal-error"))
                return QualityGateResult(findings=findings)
            return self._process_check_output(args, output, exc.returncode, code=code)

    def check(self, args: QualityGateArgs) -> QualityGateResult:
        return self._run_ruff(args, apply_fix=False, code="ruff")

    def apply(self, args: QualityGateArgs) -> QualityGateResult:
        return self._run_ruff(args, apply_fix=True, code="ruff-fix")

