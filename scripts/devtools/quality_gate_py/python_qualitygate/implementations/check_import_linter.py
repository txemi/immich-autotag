
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
        # Select configuration file based on quality level
        level = QualityLevel(args.level)
        
        match level:
            case QualityLevel.STANDARD:
                config_file = "importlinter.ini"
            case QualityLevel.TARGET:
                config_file = "importlinter-target.ini"
            case QualityLevel.STRICT:
                config_file = "importlinter-strict.ini"
        
        print(f"[INFO] Using import-linter config: {config_file} (level: {level.value})")
        
        cmd = [args.py_bin, '-m', 'importlinter', '--config', config_file]
        print(f"[RUN] {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        findings = []
        if result.returncode != 0:
            for line in result.stdout.splitlines():
                if line.strip():
                    findings.append(Finding(
                        file_path=config_file,
                        line_number=0,
                        message=line.strip(),
                        code="importlinter"
                    ))
        return CheckResult(findings=findings)

    def apply(self, args: QualityGateArgs) -> CheckResult:
        # importlinter solo checkea, no modifica
        return self.check(args)
