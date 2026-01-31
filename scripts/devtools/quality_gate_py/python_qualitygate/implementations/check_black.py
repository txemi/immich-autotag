import subprocess
from typing import Any
import attr
from python_qualitygate.core.base import Check

@attr.define(auto_attribs=True, slots=True)
class CheckBlack(Check):
    name: str = 'check_black'

    def check(self, args: Any) -> int:
        cmd = [args.py_bin, '-m', 'black', '--check', '--line-length', str(args.max_line_length), args.target_dir]
        print(f"[RUN] {' '.join(cmd)}")
        return subprocess.call(cmd)

    def apply(self, args: Any) -> int:
        cmd = [args.py_bin, '-m', 'black', '--line-length', str(args.max_line_length), args.target_dir]
        print(f"[RUN] {' '.join(cmd)}")
        return subprocess.call(cmd)
