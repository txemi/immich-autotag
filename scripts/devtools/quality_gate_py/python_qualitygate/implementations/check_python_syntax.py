
import subprocess
from pathlib import Path
from typing import Any, List
import attr
from python_qualitygate.core.base import Check
from python_qualitygate.core.result import CheckResult, Finding

@attr.define(auto_attribs=True, slots=True)
class CheckPythonSyntax(Check):
    name = 'check_python_syntax'

    def check(self, args: Any) -> CheckResult:
        py_files = list(Path(args.target_dir).rglob('*.py'))
        findings: List[Finding] = []
        for f in py_files:
            try:
                subprocess.check_call([args.py_bin, '-m', 'py_compile', str(f)])
            except subprocess.CalledProcessError as e:
                findings.append(Finding(file_path=f, line_number=0, message="Syntax error", code="syntax-error"))
        return CheckResult(findings=findings)

    def apply(self, args: Any) -> CheckResult:
        return self.check(args)
