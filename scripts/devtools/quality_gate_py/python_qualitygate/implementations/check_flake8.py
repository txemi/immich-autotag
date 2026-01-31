import subprocess
from python_qualitygate.cli.args import QualityGateArgs
import attr
from python_qualitygate.core.base import Check


@attr.define(auto_attribs=True, slots=True)
class CheckFlake8(Check):
    name = 'check_flake8'

    def check(self, args: QualityGateArgs) -> int:
        cmd = [args.py_bin, '-m', 'flake8', '--max-line-length', str(args.max_line_length), '--exclude', '.venv,immich-client,scripts,jenkins_logs', args.target_dir]
        if args.level in ('STANDARD', 'TARGET'):
            cmd += ['--extend-ignore', 'E501']
        print(f"[RUN] {' '.join(cmd)}")
        return subprocess.call(cmd)

    def apply(self, args: QualityGateArgs) -> int:
        return self.check(args)
