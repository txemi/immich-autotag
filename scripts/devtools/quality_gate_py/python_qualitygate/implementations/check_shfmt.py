import subprocess
from python_qualitygate.cli.args import QualityGateArgs
import attr
from python_qualitygate.core.base import Check


@attr.define(auto_attribs=True, slots=True)
class CheckShfmt(Check):
    name = 'check_shfmt'

    def check(self, args: QualityGateArgs) -> int:
        cmd = ['shfmt', '-d', '-i', '0']
        print(f"[RUN] {' '.join(cmd)} scripts/")
        return subprocess.call(cmd + ['scripts/'])

    def apply(self, args: QualityGateArgs) -> int:
        cmd = ['shfmt', '-w', '-i', '0']
        print(f"[RUN] {' '.join(cmd)} scripts/")
        return subprocess.call(cmd + ['scripts/'])
