import subprocess
from python_qualitygate.cli.args import QualityGateArgs
import attr
from python_qualitygate.core.base import Check


@attr.define(auto_attribs=True, slots=True)
class CheckRuff(Check):
    name = 'check_ruff'

    def check(self, args: QualityGateArgs) -> int:
        cmd = [args.py_bin, '-m', 'ruff', 'check', args.target_dir]
        if args.level in ('STANDARD', 'TARGET'):
            cmd += ['--ignore', 'E501']
        print(f"[RUN] {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            problem_lines = [line for line in result.stdout.splitlines() if line.strip()]
            print(f"[RUFF] Found {len(problem_lines)} problems.")
            print(result.stdout)
        return result.returncode

    def apply(self, args: QualityGateArgs) -> int:
        cmd = [args.py_bin, '-m', 'ruff', 'check', args.target_dir, '--fix', '--unsafe-fixes']
        if args.level in ('STANDARD', 'TARGET'):
            cmd += ['--ignore', 'E501']
        print(f"[RUN] {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            problem_lines = [line for line in result.stdout.splitlines() if line.strip()]
            print(f"[RUFF] Found {len(problem_lines)} problems.")
            print(result.stdout)
        return result.returncode
