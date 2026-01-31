import subprocess
from scripts.devtools.quality_gate_py.base import Check

class CheckRuff(Check):
    def __init__(self):
        super().__init__('check_ruff')

    def check(self, args):
        cmd = [args.py_bin, '-m', 'ruff', 'check', '--fix', args.target_dir]
        if args.level in ('STANDARD', 'TARGET'):
            cmd += ['--ignore', 'E501']
        print(f"[RUN] {' '.join(cmd)}")
        return subprocess.call(cmd)

    def apply(self, args):
        # Ruff siempre intenta arreglar con --fix
        return self.check(args)
