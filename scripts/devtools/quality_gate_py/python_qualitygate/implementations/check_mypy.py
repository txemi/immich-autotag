

from python_qualitygate.cli.args import QualityGateArgs
import attr
from python_qualitygate.core.base import Check
from python_qualitygate.core.result import CheckResult, Finding

@attr.define(auto_attribs=True, slots=True)
class CheckMypy(Check):
    name = 'check_mypy'

    def check(self, args: QualityGateArgs) -> CheckResult:
        import re
        from mypy import api as mypy_api
        print(f"[RUN] mypy API on {args.target_dir}")
        # Run mypy using its API
        stdout, stderr, exit_status = mypy_api.run(['--ignore-missing-imports', str(args.target_dir)])
        findings = []
        error_re = re.compile(r"^(.*?):(\d+): (error): (.*?)(?:\s*\[(.*?)\])?$")
        for line in stdout.splitlines():
            m = error_re.match(line.strip())
            if m:
                file_path, line_number, _, message, code = m.groups()
                findings.append(Finding(
                    file_path=file_path,
                    line_number=int(line_number),
                    message=message.strip() + (f" [{code}]" if code else ""),
                    code=code or ""
                ))
        # Determine which findings are blocking based on profile
        from python_qualitygate.core.enums_level import QualityGateLevel
        blocking = []
        nonblocking = []
        for f in findings:
            if args.level == QualityGateLevel.STRICT:
                blocking.append(f)
            elif args.level == QualityGateLevel.STANDARD:
                # STANDARD now blocks ALL mypy errors (mypy fully passes)
                blocking.append(f)
            elif args.level == QualityGateLevel.TARGET:
                # TARGET now blocks ALL mypy errors (mypy fully passes)
                blocking.append(f)
            else:
                blocking.append(f)  # Defensive: treat as STRICT
        return CheckResult(findings=blocking)

    def apply(self, args: QualityGateArgs) -> CheckResult:
        # mypy no modifica archivos, solo check
        return self.check(args)
