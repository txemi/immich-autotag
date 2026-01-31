
import re
from pathlib import Path
from python_qualitygate.cli.args import QualityGateArgs
import attr
from python_qualitygate.core.base import Check
from python_qualitygate.core.result import CheckResult, Finding

@attr.define(auto_attribs=True, slots=True)
class CheckNoDynamicAttrs(Check):
    name = 'check_no_dynamic_attrs'

    def check(self, args: QualityGateArgs) -> CheckResult:
        from python_qualitygate.core.enums_level import QualityGateLevel
        findings = []
        for pyfile in Path(args.target_dir).rglob('*.py'):
            with open(pyfile, encoding='utf-8', errors='ignore') as f:
                for i, line in enumerate(f, 1):
                    if 'getattr(' in line or 'hasattr(' in line:
                        findings.append(Finding(file_path=str(pyfile), line_number=i, message=line.strip(), code="no_dynamic_attrs"))
        # Control exhaustivo con match-case (Python 3.10+)
        match args.level:
            case QualityGateLevel.STRICT:
                return CheckResult(findings=findings)
            case QualityGateLevel.STANDARD:
                return CheckResult(findings=[])
            case QualityGateLevel.TARGET:
                return CheckResult(findings=[])
            case _:
                raise ValueError(f"Unknown QualityGateLevel: {args.level}")

    def apply(self, args: QualityGateArgs) -> CheckResult:
        # Solo checkea, no modifica
        return self.check(args)
