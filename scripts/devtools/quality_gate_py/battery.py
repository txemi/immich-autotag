from typing import List
from scripts.devtools.quality_gate_py.base import Check

class Battery:
    """Una batería es una lista ordenada de checks a ejecutar."""
    def __init__(self, checks: List[Check]):
        self.checks = checks

    def run(self, mode: str, args) -> int:
        """Ejecuta todos los checks en orden. Devuelve el primer código de error !=0 o 0 si todo OK."""
        for check in self.checks:
            if mode == 'CHECK':
                rc = check.check(args)
            elif mode == 'APPLY':
                rc = check.apply(args)
            else:
                raise ValueError(f"Modo desconocido: {mode}")
            if rc != 0:
                print(f"[FAIL] {check.name} failed")
                return rc
        print("[OK] Battery passed!")
        return 0
