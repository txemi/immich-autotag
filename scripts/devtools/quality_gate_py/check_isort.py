import subprocess
from scripts.devtools.quality_gate_py.base import Check

class CheckIsort(Check):
    def __init__(self):
        super().__init__('check_isort')

    def check(self, args):
        cmd = [args.py_bin, '-m', 'isort', '--profile', 'black', '--check-only', '--line-length', str(args.max_line_length), args.target_dir]
        print(f"[RUN] {' '.join(cmd)}")
        return subprocess.call(cmd)

    def apply(self, args):
        cmd = [args.py_bin, '-m', 'isort', '--profile', 'black', '--line-length', str(args.max_line_length), args.target_dir]
        print(f"[RUN] {' '.join(cmd)}")
        return subprocess.call(cmd)
