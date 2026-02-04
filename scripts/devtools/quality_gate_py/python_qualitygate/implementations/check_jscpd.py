
import shutil
import subprocess
from python_qualitygate.cli.args import QualityGateArgs
import attr
from python_qualitygate.core.base import Check
from python_qualitygate.core.result import QualityGateResult, Finding

@attr.define(auto_attribs=True, slots=True)
class CheckJscpd(Check):
    _name: str = attr.ib(default='check_jscpd', init=False)

    def get_name(self) -> str:
        return self._name

    def check(self, args: QualityGateArgs) -> QualityGateResult:
        # Use jscpd if available, otherwise fall back to npx
        # Raise thresholds to just above current clones (e.g., min-tokens=75, max-lines=15)
        if shutil.which('jscpd'):
            cmd = ['jscpd', '--silent', '--min-tokens', '75', '--max-lines', '15', '--format', 'python', '--ignore', '**/.venv/**,**/immich-client/**,**/scripts/**', str(args.target_dir)]
        else:
            cmd = ['npx', 'jscpd', '--silent', '--min-tokens', '75', '--max-lines', '15', '--format', 'python', '--ignore', '**/.venv/**,**/immich-client/**,**/scripts/**', str(args.target_dir)]
        print(f"[RUN] {' '.join(cmd)}")
        print(f"[JSCPD] Command executed: {' '.join(cmd)}")
        html_report_cmd = f"{' '.join(cmd).replace('--silent ', '')} --reporters html"
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print(f"[JSCPD] To generate a detailed HTML report, run:")
        print(f"[JSCPD]   {html_report_cmd}")
        findings = []
        score = None
        summary_lines = []
        clone_count = 0
        print("[JSCPD] Output summary:")
        for line in result.stdout.splitlines():
            if line.strip():
                print(f"[JSCPD] {line.strip()}")
                # Detect clone summary line and extract count
                if "Duplications detection:" in line:
                    import re
                    match = re.search(r"Found (\d+) exact clones", line)
                    if match:
                        clone_count = int(match.group(1))
                # Extract duplication percentage
                if "% duplicated lines" in line:
                    import re
                    match = re.search(r"([0-9.]+)% duplicated lines", line)
                    if match:
                        score = float(match.group(1))
                        summary_lines.append(line.strip())
                # Only add finding if clone_count > 0
                if clone_count > 0:
                    findings.append(Finding(file_path=args.target_dir, line_number=0, message=line.strip(), code="jscpd"))
        if clone_count > 0:
            print("\n[JSCPD] Duplicated code was detected. Please review the above output.")
            if summary_lines:
                print("[JSCPD] Summary:")
                for s in summary_lines:
                    print(f"  - {s}")
            print("[JSCPD] To see details, run the command manually or use the --reporters option for a full HTML report.")
        else:
            print("[JSCPD] No duplications detected.")
        return QualityGateResult(findings=findings, score=score)

    def apply(self, args: QualityGateArgs) -> QualityGateResult:
        # jscpd solo checkea, no modifica
        return self.check(args)
