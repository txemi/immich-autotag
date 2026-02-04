from dataclasses import dataclass
from typing import List

from python_qualitygate.core.base import Check
from python_qualitygate.core.enums_mode import QualityGateMode
from python_qualitygate.cli.args import QualityGateArgs

@dataclass(slots=True)
class Battery:
    """A battery is an ordered list of checks to execute."""
    checks: List[Check]

    def run(self, mode: QualityGateMode, args: QualityGateArgs) -> int:
        """Executes all checks in order. In CHECK mode, exits on first failure and prints up to 8 errors."""
        from python_qualitygate.core.enums_mode import QualityGateMode
        from python_qualitygate.core.result import CheckResult
        results = []
        for check in self.checks:
            rc, result = self._run_check(check, mode, args)
            check_name = check.get_name()
            if result.is_success():
                results.append((check_name, 'OK', 0))
            else:
                n = len(result.findings)
                results.append((check_name, f'FAIL ({n} findings)', n))
                self._print_errors(check_name, result.findings)
                self._print_summary(results)
                print(f"[EXIT] Stopped at check: {check_name} with {n} errors.")
                return n
        self._print_summary(results)
        print("[OK] Battery passed!")
        return 0

    def _run_check(self, check: Check, mode: QualityGateMode, args: QualityGateArgs):
        from python_qualitygate.core.enums_mode import QualityGateMode
        from python_qualitygate.core.result import CheckResult
        print(f"[CHECK] Running {check.get_name()} ...", flush=True)
        if mode == QualityGateMode.CHECK:
            result = check.check(args)
        elif mode == QualityGateMode.APPLY:
            result = check.apply(args)
        else:
            raise ValueError(f"Unknown mode: {mode}")
        if not isinstance(result, CheckResult):
            raise TypeError(f"Check {check.get_name()} must return a CheckResult, not {type(result)}")
        if result.is_success():
            print(f"[OK] {check.get_name()} passed\n", flush=True)
            return 0, result
        else:
            print(f"[FAIL] {check.get_name()} failed: {len(result.findings)} findings found\n", flush=True)
            return 1, result

    def _print_errors(self, check_name: str, findings) -> None:
        n = len(findings)
        for i, finding in enumerate(findings, 1):
            print(f"  [ERROR {i}] {finding.file_path}:{finding.line_number}: {finding.message}")

    def _print_summary(self, results) -> None:
        print("[SUMMARY] Quality Gate results:")
        for name, status, count in results:
            print(f"  - {name}: {status}")
