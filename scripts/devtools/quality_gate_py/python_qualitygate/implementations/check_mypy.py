
import subprocess
from python_qualitygate.cli.args import QualityGateArgs
import attr
from python_qualitygate.core.base import Check
from python_qualitygate.core.result import CheckResult, Finding

@attr.define(auto_attribs=True, slots=True)
class CheckMypy(Check):
    name = 'check_mypy'

    def check(self, args: QualityGateArgs) -> CheckResult:
        import re
        cmd: list[str] = [args.py_bin, '-m', 'mypy', '--ignore-missing-imports', args.target_dir]
        print(f"[RUN] {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        findings = []
        # Parse mypy output and extract error type
        error_re = re.compile(r"^(.*?):(\d+): (error): (.*?)(?:\s*\[(.*?)\])?$")
        for line in result.stdout.splitlines():
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
        blocking = []
        nonblocking = []
        level = args.level.value if hasattr(args.level, 'value') else str(args.level)
        for f in findings:
            # STRICT: any error blocks
            # STANDARD: only arg-type/call-arg block
            # TARGET: arg-type/call-arg/attr-defined block
            if level == "STRICT":
                blocking.append(f)
            elif level == "STANDARD":
                if f.code in ("arg-type", "call-arg"):
                    blocking.append(f)
                else:
                    nonblocking.append(f)
            elif level == "TARGET":
                if f.code in ("arg-type", "call-arg", "attr-defined"):
                    blocking.append(f)
                else:
                    nonblocking.append(f)
            else:
                blocking.append(f)  # Defensive: treat as STRICT
        # Only blocking findings are returned as errors
        return CheckResult(findings=blocking)

    def apply(self, args: QualityGateArgs) -> CheckResult:
        # mypy no modifica archivos, solo check
        return self.check(args)
