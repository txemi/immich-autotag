import subprocess
from typing import Any
import attr
from python_qualitygate.core.base import Check

@attr.define(auto_attribs=True, slots=True)
class CheckNoTuples(Check):
    name: str = 'check_no_tuples'

    def check(self, args: Any) -> int:
        script = 'scripts/devtools/check_no_tuples.py'
        cmd: list[str] = [args.py_bin, script, args.target_dir, '--exclude', '.venv,immich-client,scripts']
        print(f"[RUN] {' '.join(cmd)}")
        return subprocess.call(cmd)

    def apply(self, args: Any) -> int:
        return self.check(args)
