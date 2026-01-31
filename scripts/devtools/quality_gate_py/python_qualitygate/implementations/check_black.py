import subprocess
from python_qualitygate.cli.args import QualityGateArgs
import attr
from python_qualitygate.core.base import Check


@attr.define(auto_attribs=True, slots=True)
class CheckBlack(Check):
    name = 'check_black'

    def check(self, args: QualityGateArgs) -> int:
        cmd = [args.py_bin, '-m', 'black', '--check', '--line-length', str(args.max_line_length), args.target_dir]
        print(f"[RUN] {' '.join(cmd)}")
        return subprocess.call(cmd)

    def apply(self, args: QualityGateArgs) -> int:
        cmd = [args.py_bin, '-m', 'black', '--line-length', str(args.max_line_length), args.target_dir]
        print(f"[RUN] {' '.join(cmd)}")
        return subprocess.call(cmd)
