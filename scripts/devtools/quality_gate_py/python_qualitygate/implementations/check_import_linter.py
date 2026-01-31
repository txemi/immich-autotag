import subprocess
from typing import Any
import attr
from python_qualitygate.core.base import Check

@attr.define(auto_attribs=True, slots=True)
class CheckImportLinter(Check):
    name: str = 'check_import_linter'

    def check(self, args: Any) -> int:
        cmd = [args.py_bin, '-m', 'importlinter', '--config', 'importlinter.ini']
        print(f"[RUN] {' '.join(cmd)}")
        return subprocess.call(cmd)

    def apply(self, args: Any) -> int:
        return self.check(args)
