
import subprocess
from python_qualitygate.cli.args import QualityGateArgs
import attr
from python_qualitygate.core.base import Check
from python_qualitygate.core.result import CheckResult, Finding

@attr.define(auto_attribs=True, slots=True)
class CheckBlack(Check):
    name = 'check_black'

    def check(self, args: QualityGateArgs) -> CheckResult:
        cmd = [args.py_bin, '-m', 'black', '--check', '--line-length', str(args.max_line_length), args.target_dir]
        print(f"[RUN] {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        findings = []
        if result.returncode != 0:
            # Parsear archivos afectados del output de black
            for line in result.stdout.splitlines():
                if line.strip().endswith('would reformat'):
                    file_path = line.split()[0]
                    findings.append(Finding(file_path=file_path, line_number=0, message="Archivo sin formato black", code="black-format"))
            if not findings:
                findings.append(Finding(file_path=args.target_dir, line_number=0, message="Black encontró errores de formato", code="black-format"))
        return CheckResult(findings=findings)

    def apply(self, args: QualityGateArgs) -> CheckResult:
        cmd = [args.py_bin, '-m', 'black', '--line-length', str(args.max_line_length), args.target_dir]
        print(f"[RUN] {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        findings = []
        if result.returncode != 0:
            findings.append(Finding(file_path=args.target_dir, line_number=0, message="Black no pudo formatear todos los archivos", code="black-apply-error"))
        return CheckResult(findings=findings)
