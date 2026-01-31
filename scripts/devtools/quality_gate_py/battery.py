from typing import List
from scripts.devtools.quality_gate_py.base import Check


class Battery:
    """A battery is an ordered list of checks to execute."""
    def __init__(self, checks: List[Check]):
        self.checks = checks

    def run(self, mode: str, args) -> int:
        """Executes all checks in order. Returns the first error code !=0 or 0 if all OK."""
        for check in self.checks:
            if mode == 'CHECK':
                rc = check.check(args)
            elif mode == 'APPLY':
                rc = check.apply(args)
            else:
                raise ValueError(f"Unknown mode: {mode}")
            if rc != 0:
                print(f"[FAIL] {check.name} failed")
                return rc
        print("[OK] Battery passed!")
        return 0
