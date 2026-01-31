import subprocess
from typing import Any
import attr
from python_qualitygate.core.base import Check

@attr.define(auto_attribs=True, slots=True)
class CheckMypy(Check):
    name: str = 'check_mypy'

    def check(self, args: Any) -> int:
        cmd: list[str] = [args.py_bin, '-m', 'mypy', '--ignore-missing-imports', args.target_dir]
        print(f"[RUN] {' '.join(cmd)}")
        return subprocess.call(cmd)

    def apply(self, args: Any) -> int:
        return self.check(args)
