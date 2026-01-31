import subprocess
from scripts.devtools.quality_gate_py.base import Check

class CheckImportLinter(Check):
    def __init__(self):
        super().__init__('check_import_linter')

    def check(self, args):
        cmd = [args.py_bin, '-m', 'importlinter', '--config', 'importlinter.ini']
        print(f"[RUN] {' '.join(cmd)}")
        return subprocess.call(cmd)

    def apply(self, args):
        # Solo reporta
        return self.check(args)
