import subprocess
from python_qualitygate.base import Check

class CheckFlake8(Check):
    def __init__(self):
        super().__init__('check_flake8')

    def check(self, args):
        cmd = [args.py_bin, '-m', 'flake8', '--max-line-length', str(args.max_line_length), '--exclude', '.venv,immich-client,scripts,jenkins_logs', args.target_dir]
        if args.level in ('STANDARD', 'TARGET'):
            cmd += ['--extend-ignore', 'E501']
        print(f"[RUN] {' '.join(cmd)}")
        return subprocess.call(cmd)

    def apply(self, args):
        # Flake8 solo reporta, no modifica
        return self.check(args)
