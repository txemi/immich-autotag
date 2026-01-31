import subprocess
from python_qualitygate.base import Check

class CheckShfmt(Check):
    def __init__(self):
        super().__init__('check_shfmt')

    def check(self, args):
        cmd = ['shfmt', '-d', '-i', '0']
        print(f"[RUN] {' '.join(cmd)} scripts/")
        return subprocess.call(cmd + ['scripts/'])

    def apply(self, args):
        cmd = ['shfmt', '-w', '-i', '0']
        print(f"[RUN] {' '.join(cmd)} scripts/")
        return subprocess.call(cmd + ['scripts/'])
