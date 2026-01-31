from typing import List
from scripts.devtools.quality_gate_py.base import Check

class Battery:
    """Una batería es una lista ordenada de checks a ejecutar."""
    def __init__(self, checks: List[Check]):
        self.checks = checks

    def run(self, mode: str, args) -> int:
        """Ejecuta todos los checks en orden. Devuelve el primer código de error !=0 o 0 si todo OK."""
        results = []
        for check in self.checks:
            print(f"[CHECK] Running {check.name} ...", flush=True)
            if mode == 'CHECK':
                rc = check.check(args)
            elif mode == 'APPLY':
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
