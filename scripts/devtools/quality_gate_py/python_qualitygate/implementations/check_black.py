import subprocess
from python_qualitygate.base import Check

class CheckBlack(Check):
    def __init__(self):
        super().__init__('check_black')

    def check(self, args):
        cmd = [args.py_bin, '-m', 'black', '--check', '--line-length', str(args.max_line_length), args.target_dir]
        print(f"[RUN] {' '.join(cmd)}")
        return subprocess.call(cmd)

    def apply(self, args):
        cmd = [args.py_bin, '-m', 'black', '--line-length', str(args.max_line_length), args.target_dir]
        print(f"[RUN] {' '.join(cmd)}")
        return subprocess.call(cmd)
