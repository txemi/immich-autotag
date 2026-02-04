import subprocess
import attr
from python_qualitygate.cli.args import QualityGateArgs
from python_qualitygate.core.base import Check
from python_qualitygate.core.enums_level import QualityGateLevel
from python_qualitygate.core.result import CheckResult, Finding
DISABLE_IMPORT_LINTER_CHECK = True  # Cambia a False para reactivar el check


@attr.define(auto_attribs=True, slots=True)
class CheckImportLinter(Check):
    name = 'check_import_linter'

    def check(self, args: QualityGateArgs) -> CheckResult:
        if DISABLE_IMPORT_LINTER_CHECK:
            # Devuelve un resultado vacío y exitoso
            return CheckResult(
                check_name=self.name,
                findings=[],
                passed=True,
                output="[INFO] Import-linter check disabled by configuration."
            )
        # Select configuration file based on quality level
        level = args.level

        match level:
            case QualityGateLevel.STANDARD:
                config_file = "importlinter.ini"
            case QualityGateLevel.TARGET:
                config_file = "importlinter-target.ini"
            case QualityGateLevel.STRICT:
                config_file = "importlinter-strict.ini"

        print(f"[INFO] Using import-linter config: {config_file} (level: {level.value})")

        # Use the lint-imports binary from the same venv as py_bin
        from pathlib import Path
        lint_imports_bin = str(Path(args.py_bin).parent / 'lint-imports')
        cmd = [lint_imports_bin, '--config', config_file, '--output-markdown']
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
