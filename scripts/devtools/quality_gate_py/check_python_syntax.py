import subprocess
from pathlib import Path
from scripts.devtools.quality_gate_py.base import Check

class CheckPythonSyntax(Check):
    def __init__(self):
        super().__init__('check_python_syntax')

    def check(self, args):
        py_files = list(Path(args.target_dir).rglob('*.py'))
        failed = False
        for f in py_files:
            try:
                subprocess.check_call([args.py_bin, '-m', 'py_compile', str(f)])
            except subprocess.CalledProcessError:
                print(f"[ERROR] Syntax error in {f}")
                failed = True
        return 1 if failed else 0

    def apply(self, args):
        # No modifica nada, igual que check
        return self.check(args)
