import subprocess
from pathlib import Path
from typing import Any
import attr
from python_qualitygate.core.base import Check


@attr.define(auto_attribs=True, slots=True)
class CheckPythonSyntax(Check):
    name = 'check_python_syntax'

    def check(self, args: Any) -> int:
        py_files = list(Path(args.target_dir).rglob('*.py'))
        failed = False
        for f in py_files:
            try:
                subprocess.check_call([args.py_bin, '-m', 'py_compile', str(f)])
            except subprocess.CalledProcessError:
                print(f"[ERROR] Syntax error in {f}")
                failed = True
        return 1 if failed else 0

    def apply(self, args: Any) -> int:
        return self.check(args)
