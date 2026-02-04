
import subprocess
from python_qualitygate.cli.args import QualityGateArgs
import attr
from python_qualitygate.core.base import Check
from python_qualitygate.core.result import CheckResult, Finding

@attr.define(auto_attribs=True, slots=True)
class CheckNoTuples(Check):
    _name: str = attr.ib(default='check_no_tuples', init=False)

    def get_name(self) -> str:
        return self._name

    def check(self, args: QualityGateArgs) -> CheckResult:
        script = 'scripts/devtools/check_no_tuples.py'
        cmd = [str(args.py_bin), str(script), str(args.target_dir), '--exclude', '.venv,immich-client,scripts']
        print(f"[RUN] {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        findings = []
        if result.returncode != 0:
            for line in result.stdout.splitlines():
                if line.strip():
                    findings.append(Finding(file_path=args.target_dir, line_number=0, message=line.strip(), code="no_tuples"))
        return CheckResult(findings=findings)

    def apply(self, args: QualityGateArgs) -> CheckResult:
        # Este check solo checkea, no modifica
        return self.check(args)
