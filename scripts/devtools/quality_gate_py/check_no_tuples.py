import subprocess
from scripts.devtools.quality_gate_py.base import Check

class CheckNoTuples(Check):
    def __init__(self):
        super().__init__('check_no_tuples')

    def check(self, args):
        script = 'scripts/devtools/check_no_tuples.py'
        cmd = [args.py_bin, script, args.target_dir, '--exclude', '.venv,immich-client,scripts']
        print(f"[RUN] {' '.join(cmd)}")
        return subprocess.call(cmd)

    def apply(self, args):
        # Solo reporta
        return self.check(args)
