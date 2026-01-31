import subprocess
from python_qualitygate.base import Check

class CheckRuff(Check):
    def __init__(self):
        super().__init__('check_ruff')

    def check(self, args):
            cmd = [args.py_bin, '-m', 'ruff', 'check', args.target_dir]
            if args.level in ('STANDARD', 'TARGET'):
                cmd += ['--ignore', 'E501']
            print(f"[RUN] {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                # Ruff outputs one line per problem, so count lines in stdout
                problem_lines = [line for line in result.stdout.splitlines() if line.strip()]
                print(f"[RUFF] Found {len(problem_lines)} problems.")
                print(result.stdout)
            return result.returncode

    def apply(self, args):
        # Enable Ruff's --unsafe-fixes option in APPLY mode
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
