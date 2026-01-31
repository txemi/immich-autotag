from dataclasses import dataclass
from typing import List
from python_qualitygate.core.base import Check

@dataclass(slots=True)
class Battery:
    """A battery is an ordered list of checks to execute."""
    checks: List[Check]

    def run(self, mode, args) -> int:
        """Executes all checks in order. Returns 0 if all OK, or the number of findings if any check fails."""
        from python_qualitygate.core.enums_mode import QualityGateMode
        from python_qualitygate.core.result import CheckResult
        results = []
        for check in self.checks:
            print(f"[CHECK] Running {check.name} ...", flush=True)
            if mode == QualityGateMode.CHECK:
                result = check.check(args)
            elif mode == QualityGateMode.APPLY:
                result = check.apply(args)
            else:
                raise ValueError(f"Modo desconocido: {mode}")
            if not isinstance(result, CheckResult):
                raise TypeError(f"El check {check.name} debe devolver un CheckResult, no {type(result)}")
            if result.is_success():
                print(f"[OK] {check.name} passed\n", flush=True)
                results.append((check.name, 'OK', 0))
            else:
                n = len(result.findings)
                print(f"[FAIL] {check.name} failed: {n} incidencias encontradas\n", flush=True)
                for finding in result.findings:
                    print(f"  [ERROR] {finding.file_path}:{finding.line_number}: {finding.message}")
                results.append((check.name, f'FAIL ({n} incidencias)', n))
                print("[SUMMARY] Quality Gate results:")
                for name, status, count in results:
                    print(f"  - {name}: {status}")
                return n
        print("[SUMMARY] Quality Gate results:")
        for name, status, count in results:
            print(f"  - {name}: {status}")
        print("[OK] Battery passed!")
        return 0
