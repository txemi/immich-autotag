import subprocess
from typing import Any
import attr
from python_qualitygate.core.base import Check

@attr.define(auto_attribs=True, slots=True)
class CheckShfmt(Check):
    name: str = 'check_shfmt'

    def check(self, args: Any) -> int:
        cmd = ['shfmt', '-d', '-i', '0']
        print(f"[RUN] {' '.join(cmd)} scripts/")
        return subprocess.call(cmd + ['scripts/'])

    def apply(self, args: Any) -> int:
        cmd = ['shfmt', '-w', '-i', '0']
        print(f"[RUN] {' '.join(cmd)} scripts/")
        return subprocess.call(cmd + ['scripts/'])
