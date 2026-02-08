import subprocess
from python_qualitygate.core.result import Finding, QualityGateResult


from typing import Callable, List, Any

def run_subprocess_and_process(
    cmd: List[str],
    process_line_fn: Callable[[str], Any],
    error_code: int,
    target_dir: str,
    code: str,
    print_cmd: bool = True
) -> QualityGateResult:
    if print_cmd:
        print(f"[RUN] {' '.join(cmd)}")
    findings = []
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return QualityGateResult(findings=[])
    except subprocess.CalledProcessError as exc:
        output = exc.stdout or exc.stderr or ""
        if exc.returncode == error_code:
            for line in output.splitlines():
                finding = process_line_fn(line)
                if finding:
                    findings.append(finding)
            if not findings:
                msg = output.strip() or f"Tool found errors (code {code})"
                findings.append(Finding(file_path=target_dir, line_number=0, message=msg, code=code))
        else:
            error_msg = f"Tool failed with exit code {exc.returncode}: {exc}"
            findings.append(Finding(file_path=target_dir, line_number=0, message=error_msg, code=f"{code}-apply-error"))
            if exc.stderr:
                for line in exc.stderr.splitlines():
                    if line.strip():
                        findings.append(Finding(file_path=target_dir, line_number=0, message=line.strip(), code=f"{code}-apply-error"))
        return QualityGateResult(findings=findings)
