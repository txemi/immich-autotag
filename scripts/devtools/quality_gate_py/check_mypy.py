import subprocess
from scripts.devtools.quality_gate_py.base import Check

class CheckMypy(Check):
    def __init__(self):
        super().__init__('check_mypy')

    def check(self, args):
        cmd = [args.py_bin, '-m', 'mypy', '--ignore-missing-imports', args.target_dir]
        print(f"[RUN] {' '.join(cmd)}")
        return subprocess.call(cmd)

    def apply(self, args):
        # Mypy solo reporta, no modifica
        return self.check(args)
