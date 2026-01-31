import subprocess
from python_qualitygate.cli.args import QualityGateArgs
import attr
from python_qualitygate.core.base import Check


@attr.define(auto_attribs=True, slots=True)
class CheckSsort(Check):
    name = 'check_ssort'

    def check(self, args: QualityGateArgs) -> int:
        cmd = ['ssort', '--check', args.target_dir]
        print(f"[RUN] {' '.join(cmd)}")
        return subprocess.call(cmd)

    def apply(self, args: QualityGateArgs) -> int:
        cmd = ['ssort', args.target_dir]
        print(f"[RUN] {' '.join(cmd)}")
        return subprocess.call(cmd)
