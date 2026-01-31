import subprocess
from python_qualitygate.base import Check

class CheckSsort(Check):
    def __init__(self):
        super().__init__('check_ssort')

    def check(self, args):
        cmd = ['ssort', '--check', args.target_dir]
        print(f"[RUN] {' '.join(cmd)}")
        return subprocess.call(cmd)

    def apply(self, args):
        cmd = ['ssort', args.target_dir]
        print(f"[RUN] {' '.join(cmd)}")
        return subprocess.call(cmd)
