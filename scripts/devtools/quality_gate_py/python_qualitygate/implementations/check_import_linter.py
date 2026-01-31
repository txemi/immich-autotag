import subprocess
from python_qualitygate.cli.args import QualityGateArgs
import attr
from python_qualitygate.core.base import Check


@attr.define(auto_attribs=True, slots=True)
class CheckImportLinter(Check):
    name = 'check_import_linter'

    def check(self, args: QualityGateArgs) -> int:
        cmd = [args.py_bin, '-m', 'importlinter', '--config', 'importlinter.ini']
        print(f"[RUN] {' '.join(cmd)}")
        return subprocess.call(cmd)

    def apply(self, args: QualityGateArgs) -> int:
        return self.check(args)
