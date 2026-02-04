import attr
from pathlib import Path
from python_qualitygate.cli.args import QualityGateArgs
from python_qualitygate.core.base import Check
from python_qualitygate.core.result import QualityGateResult, Finding

@attr.define(auto_attribs=True, slots=True)
class CheckLargeFiles(Check):
    _name: str = attr.ib(default='check_large_files', init=False)
    # Reasonable threshold: 1000 lines per Python file
    MAX_LINES_STANDARD: int = 1080
    MAX_LINES_TARGET: int = 1020

    def get_name(self) -> str:
        return self._name

    def check(self, args: QualityGateArgs) -> QualityGateResult:
        from python_qualitygate.core.enums_level import QualityGateLevel
        if args.level == QualityGateLevel.STANDARD:
            max_lines = self.MAX_LINES_STANDARD
        elif args.level in (QualityGateLevel.STRICT, QualityGateLevel.TARGET):
            max_lines = self.MAX_LINES_TARGET
        else:
            raise ValueError(f"Unknown QualityGateLevel: {args.level}")
        findings = []
        for pyfile in Path(args.target_dir).rglob('*.py'):
            # Exclude common folders
            if any(skip in str(pyfile) for skip in ['.venv', 'immich-client', 'scripts', 'jenkins_logs']):
                continue
            try:
                with open(pyfile, encoding='utf-8', errors='ignore') as f:
                    num_lines = sum(1 for _ in f)
                if num_lines > max_lines:
                    findings.append(Finding(
                        file_path=str(pyfile),
                        line_number=0,
                        message=f"File exceeds {max_lines} lines ({num_lines} lines)",
                        code="large-file"
                    ))
            except Exception as e:
                findings.append(Finding(
                    file_path=str(pyfile),
                    line_number=0,
                    message=f"Error reading file: {e}",
                    code="large-file-error"
                ))
        return QualityGateResult(findings=findings)

    def apply(self, args: QualityGateArgs) -> QualityGateResult:
        # Solo checkea, no modifica
        return self.check(args)
