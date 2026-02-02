
import subprocess
from enum import Enum
from python_qualitygate.cli.args import QualityGateArgs
import attr
from python_qualitygate.core.base import Check
from python_qualitygate.core.result import CheckResult, Finding


class QualityLevel(str, Enum):
    STANDARD = "STANDARD"
    TARGET = "TARGET"
    STRICT = "STRICT"


@attr.define(auto_attribs=True, slots=True)
class CheckImportLinter(Check):
    name = 'check_import_linter'

    def check(self, args: QualityGateArgs) -> CheckResult:
        # Only run in TARGET or STRICT levels, skip in STANDARD
        level = QualityLevel(args.level)
        
        match level:
            case QualityLevel.STANDARD:
                print(f"[SKIP] import-linter skipped in {level.value} level (only runs in TARGET/STRICT)")
                return CheckResult(findings=[])
            case QualityLevel.TARGET | QualityLevel.STRICT:
                cmd = [args.py_bin, '-m', 'importlinter', '--config', 'importlinter.ini']
                print(f"[RUN] {' '.join(cmd)}")
                result = subprocess.run(cmd, capture_output=True, text=True)
                findings = []
                if result.returncode != 0:
                    for line in result.stdout.splitlines():
                        if line.strip():
                            findings.append(Finding(
                                file_path='importlinter.ini',
                                line_number=0,
                                message=line.strip(),
                                code="importlinter"
                            ))
                return CheckResult(findings=findings)

    def apply(self, args: QualityGateArgs) -> CheckResult:
        # importlinter solo checkea, no modifica
        return self.check(args)
