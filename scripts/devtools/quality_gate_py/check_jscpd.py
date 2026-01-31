import subprocess
from scripts.devtools.quality_gate_py.base import Check

class CheckJscpd(Check):
    def __init__(self):
        super().__init__('check_jscpd')

    def check(self, args):
        cmd = ['jscpd', '--silent', '--min-tokens', '30', '--max-lines', '100', '--format', 'python', '--ignore', '**/.venv/**,**/immich-client/**,**/scripts/**', args.target_dir]
        print(f"[RUN] {' '.join(cmd)}")
        return subprocess.call(cmd)

    def apply(self, args):
        # jscpd solo reporta, no modifica
        return self.check(args)
