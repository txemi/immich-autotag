import subprocess
import attr
from python_qualitygate.core.base import Check
from python_qualitygate.core.result import QualityGateResult, Finding
from python_qualitygate.cli.args import QualityGateArgs


@attr.define(auto_attribs=True, slots=True)
class CheckPylintProtectedAccess(Check):
    _name: str = attr.ib(default='check_pylint_protected_access', init=False)

    def get_name(self) -> str:
        return self._name

    def check(self, args: QualityGateArgs) -> QualityGateResult:
        from python_qualitygate.core.enums_level import QualityGateLevel

        import re
        from typing import Callable, Optional
        def _run_and_parse_pylint(args: QualityGateArgs, finding_filter: Optional[Callable[[Finding], bool]] = None):
            cmd = [args.py_bin, '-m', 'pylint', str(args.target_dir)]
            print(f"[RUN] {' '.join(cmd)}")
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, check=False)
            except Exception as e:
                raise RuntimeError(f"Error running pylint: {e}")

            # If pylint is not installed or module not found, raise exception
            if result.stderr and ("No module named pylint" in result.stderr or result.returncode == 1 and "No module named" in result.stderr):
                raise RuntimeError(f"pylint is not installed or module not found: {result.stderr.strip()}")

            from pathlib import Path
            findings: list[Finding] = []
            score = None
            if result.stderr.strip():
                findings.append(Finding(
                    file_path=Path("pylint"),
                    line_number=0,
                    message=f"stderr: {result.stderr.strip()}",
                    code="pylint-stderr"
                ))
            # Always process findings, even if returncode != 0
            for line in result.stdout.splitlines():
                # Extract pylint score
                score_match = re.search(r"Your code has been rated at ([0-9.]+)/10", line)
                if score_match:
                    score = float(score_match.group(1))
                if ":" in line:
                    parts = line.split(":", 4)
                    if len(parts) >= 5:
                        file_path, line_number, _, code, message = [p.strip() for p in parts]
                        finding = Finding(
                            file_path=Path(file_path),
                            line_number=int(line_number) if line_number.isdigit() else 0,
                            message=message,
                            code=code
                        )
                        if finding_filter is None or finding_filter(finding):
                            findings.append(finding)
            return findings, score

        match args.level:
            case QualityGateLevel.STRICT:
                findings, score = _run_and_parse_pylint(args)
                return QualityGateResult(findings=findings, score=score)
            case QualityGateLevel.TARGET | QualityGateLevel.STANDARD:
                findings, score = _run_and_parse_pylint(args, finding_filter=lambda f: f.code == "W0212")
                return QualityGateResult(findings=findings, score=score)
            case _:
                raise ValueError(f"Unknown QualityGateLevel: {args.level}")

    def apply(self, args: QualityGateArgs) -> QualityGateResult:
        return self.check(args)
