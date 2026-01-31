

import py_compile
from pathlib import Path
from typing import List
from python_qualitygate.cli.args import QualityGateArgs
import attr
from python_qualitygate.core.base import Check
from python_qualitygate.core.result import CheckResult, Finding

@attr.define(auto_attribs=True, slots=True)
class CheckPythonSyntax(Check):
    name = 'check_python_syntax'


    def check(self, args: QualityGateArgs) -> CheckResult:
        py_files = list(Path(args.target_dir).rglob('*.py'))
        findings: List[Finding] = []
        for f in py_files:
            try:
                py_compile.compile(str(f), doraise=True)
            except py_compile.PyCompileError as e:
                # Extract message and line if possible
                msg = str(e)
                lineno = 0
                if hasattr(e, 'exc_value') and hasattr(e.exc_value, 'lineno'):
                    lineno = getattr(e.exc_value, 'lineno', 0)
                findings.append(Finding(file_path=f, line_number=lineno, message=msg, code="syntax-error"))
        return CheckResult(findings=findings)

    def apply(self, args: QualityGateArgs) -> CheckResult:
        return self.check(args)
