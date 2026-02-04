
import subprocess
from python_qualitygate.cli.args import QualityGateArgs
import attr
from python_qualitygate.core.base import Check
from python_qualitygate.core.result import CheckResult, Finding

@attr.define(auto_attribs=True, slots=True)
class CheckSsort(Check):
    _name: str = attr.ib(default='check_ssort', init=False)

    def get_name(self) -> str:
        return self._name


    def check(self, args: QualityGateArgs) -> CheckResult:
        import sys
        import io
        import ssort._main
        old_argv = sys.argv.copy()
        sys.argv = ['ssort', '--check', str(args.target_dir)]
        stdout = io.StringIO()
        stderr = io.StringIO()
        old_stdout, old_stderr = sys.stdout, sys.stderr
        sys.stdout, sys.stderr = stdout, stderr
        findings = []
        try:
            ssort._main.main()
            output = stdout.getvalue()
            # ssort --check prints summary even if OK, only findings if there are errors
            # If there is "would be left unchanged" we consider it OK
            if 'would be left unchanged' not in output:
                for line in output.splitlines():
                    if line.strip():
                        findings.append(Finding(file_path=args.target_dir, line_number=0, message=line.strip(), code="ssort"))
        except SystemExit as e:
            output = stdout.getvalue()
            if e.code != 0:
                for line in output.splitlines():
                    if line.strip():
                        findings.append(Finding(file_path=args.target_dir, line_number=0, message=line.strip(), code="ssort"))
        finally:
            sys.stdout, sys.stderr = old_stdout, old_stderr
            sys.argv = old_argv
        return CheckResult(findings=findings)

    def apply(self, args: QualityGateArgs) -> CheckResult:
        import sys
        import io
        import ssort._main
        old_argv = sys.argv.copy()
        sys.argv = ['ssort', str(args.target_dir)]
        stdout = io.StringIO()
        stderr = io.StringIO()
        old_stdout, old_stderr = sys.stdout, sys.stderr
        sys.stdout, sys.stderr = stdout, stderr
        findings = []
        try:
            ssort._main.main()
            output = stdout.getvalue()
            if 'would be left unchanged' not in output:
                for line in output.splitlines():
                    if line.strip():
                        findings.append(Finding(file_path=args.target_dir, line_number=0, message=line.strip(), code="ssort"))
        except SystemExit as e:
            output = stdout.getvalue()
            if e.code != 0:
                for line in output.splitlines():
                    if line.strip():
                        findings.append(Finding(file_path=args.target_dir, line_number=0, message=line.strip(), code="ssort"))
        finally:
            sys.stdout, sys.stderr = old_stdout, old_stderr
            sys.argv = old_argv
        return CheckResult(findings=findings)
