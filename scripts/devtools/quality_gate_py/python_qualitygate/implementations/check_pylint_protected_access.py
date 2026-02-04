import subprocess
import attr
from python_qualitygate.core.base import Check
from python_qualitygate.core.result import CheckResult, Finding
from python_qualitygate.cli.args import QualityGateArgs


@attr.define(auto_attribs=True, slots=True)
class CheckPylintProtectedAccess(Check):
    _name: str = attr.ib(default='check_pylint_protected_access', init=False)

    def get_name(self) -> str:
        return self._name

    def check(self, args: QualityGateArgs) -> CheckResult:
        from python_qualitygate.core.enums_level import QualityGateLevel

        def _run_and_parse_pylint(args, finding_filter=None):
            cmd = [args.py_bin, '-m', 'pylint', str(args.target_dir)]
            print(f"[RUN] {' '.join(cmd)}")
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, check=False)
            except Exception as e:
                raise RuntimeError(f"Error running pylint: {e}")

            # If pylint is not installed or module not found, raise exception
            if result.stderr and ("No module named pylint" in result.stderr or result.returncode == 1 and "No module named" in result.stderr):
                raise RuntimeError(f"pylint is not installed or module not found: {result.stderr.strip()}")

            findings = []
            if result.stderr.strip():
                findings.append(Finding(
                    file_path="pylint",
                    line_number=0,
                    message=f"stderr: {result.stderr.strip()}",
                    code="pylint-stderr"
                ))
            # Always process findings, even if returncode != 0
            for line in result.stdout.splitlines():
                if ":" in line:
                    parts = line.split(":", 4)
                    if len(parts) >= 5:
                        file_path, line_number, col, code, message = [p.strip() for p in parts]
                        finding = Finding(
                            file_path=file_path,
                            line_number=int(line_number) if line_number.isdigit() else 0,
                            message=message,
                            code=code
                        )
                        if finding_filter is None or finding_filter(finding):
                            findings.append(finding)
            return findings

        match args.level:
            case QualityGateLevel.STRICT:
                # Block ALL pylint findings in STRICT
                findings = _run_and_parse_pylint(args)
                return CheckResult(findings=findings)
            case QualityGateLevel.TARGET:
                # Block ONLY protected-access (W0212) in TARGET
                findings = _run_and_parse_pylint(args, finding_filter=lambda f: f.code == "W0212")
                return CheckResult(findings=findings)
            case QualityGateLevel.STANDARD:
                # Do not block in STANDARD
                return CheckResult(findings=[])
            case _:
                raise ValueError(f"Unknown QualityGateLevel: {args.level}")

    def apply(self, args: QualityGateArgs) -> CheckResult:
        return self.check(args)
