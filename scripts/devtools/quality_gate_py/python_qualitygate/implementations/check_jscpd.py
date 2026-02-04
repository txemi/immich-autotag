
import shutil
import subprocess
from python_qualitygate.cli.args import QualityGateArgs
import attr
from python_qualitygate.core.base import Check
from python_qualitygate.core.result import CheckResult, Finding

@attr.define(auto_attribs=True, slots=True)
class CheckJscpd(Check):
    _name: str = attr.ib(default='check_jscpd', init=False)

    def get_name(self) -> str:
        return self._name

    def check(self, args: QualityGateArgs) -> CheckResult:
        # Use jscpd if available, otherwise fall back to npx
        if shutil.which('jscpd'):
            cmd = ['jscpd', '--silent', '--min-tokens', '30', '--max-lines', '100', '--format', 'python', '--ignore', '**/.venv/**,**/immich-client/**,**/scripts/**', str(args.target_dir)]
        else:
            cmd = ['npx', 'jscpd', '--silent', '--min-tokens', '30', '--max-lines', '100', '--format', 'python', '--ignore', '**/.venv/**,**/immich-client/**,**/scripts/**', str(args.target_dir)]
        print(f"[RUN] {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        findings = []
        if result.returncode != 0:
            for line in result.stdout.splitlines():
                if line.strip():
                    findings.append(Finding(file_path=args.target_dir, line_number=0, message=line.strip(), code="jscpd"))
        return CheckResult(findings=findings)

    def apply(self, args: QualityGateArgs) -> CheckResult:
        # jscpd solo checkea, no modifica
        return self.check(args)
