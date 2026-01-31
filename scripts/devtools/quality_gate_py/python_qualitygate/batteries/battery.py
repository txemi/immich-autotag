from dataclasses import dataclass
from typing import List
from python_qualitygate.core.base import Check

@dataclass(slots=True)
class Battery:
    """A battery is an ordered list of checks to execute."""
    checks: List[Check]

    def run(self, mode, args) -> int:
        """Executes all checks in order. Returns the first error code !=0 or 0 if all OK."""
        from python_qualitygate.core.enums_mode import QualityGateMode
        results = []
        for check in self.checks:
            print(f"[CHECK] Running {check.name} ...", flush=True)
            if mode == QualityGateMode.CHECK:
                rc = check.check(args)
            elif mode == QualityGateMode.APPLY:
                rc = check.apply(args)
            else:
                raise ValueError(f"Modo desconocido: {mode}")
            if rc == 0:
                print(f"[OK] {check.name} passed\n", flush=True)
                results.append((check.name, 'OK'))
            else:
                print(f"[FAIL] {check.name} failed (rc={rc})\n", flush=True)
                results.append((check.name, f'FAIL ({rc})'))
                print("[SUMMARY] Quality Gate results:")
                for name, status in results:
                    print(f"  - {name}: {status}")
                return rc
        print("[SUMMARY] Quality Gate results:")
        for name, status in results:
            print(f"  - {name}: {status}")
        print("[OK] Battery passed!")
        return 0
