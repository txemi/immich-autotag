import attr
from pathlib import Path
from python_qualitygate.cli.args import QualityGateArgs
from python_qualitygate.core.base import Check
from python_qualitygate.core.result import CheckResult, Finding

@attr.define(auto_attribs=True, slots=True)
class CheckLargeFiles(Check):
    _name: str = attr.ib(default='check_large_files', init=False)
    # Umbral razonable: 1000 líneas por archivo Python
    MAX_LINES: int = 1000

    def get_name(self) -> str:
        return self._name

    def check(self, args: QualityGateArgs) -> CheckResult:
        from python_qualitygate.core.enums_level import QualityGateLevel
        match args.level:
            case QualityGateLevel.STRICT:
                pass  # Ejecutar el check normalmente
            case QualityGateLevel.STANDARD | QualityGateLevel.TARGET:
                # No activo en estos modos
                return CheckResult(findings=[])
            case _:
                # Programación defensiva: si aparece un nivel desconocido, bloquear
                raise ValueError(f"Unknown QualityGateLevel: {args.level}")
        findings = []
        for pyfile in Path(args.target_dir).rglob('*.py'):
            # Excluir carpetas típicas
            if any(skip in str(pyfile) for skip in ['.venv', 'immich-client', 'scripts', 'jenkins_logs']):
                continue
            try:
                with open(pyfile, encoding='utf-8', errors='ignore') as f:
                    num_lines = sum(1 for _ in f)
                if num_lines > self.MAX_LINES:
                    findings.append(Finding(
                        file_path=str(pyfile),
                        line_number=0,
                        message=f"File exceeds {self.MAX_LINES} lines ({num_lines} lines)",
                        code="large-file"
                    ))
            except Exception as e:
                findings.append(Finding(
                    file_path=str(pyfile),
                    line_number=0,
                    message=f"Error reading file: {e}",
                    code="large-file-error"
                ))
        return CheckResult(findings=findings)

    def apply(self, args: QualityGateArgs) -> CheckResult:
        # Solo checkea, no modifica
        return self.check(args)
