import subprocess
import re
from pathlib import Path
from python_qualitygate.base import Check

class CheckNoDynamicAttrs(Check):
    def __init__(self):
        super().__init__('check_no_dynamic_attrs')

    def check(self, args):
        failed = False
        for pyfile in Path(args.target_dir).rglob('*.py'):
            with open(pyfile, encoding='utf-8', errors='ignore') as f:
                for i, line in enumerate(f, 1):
                    if 'getattr(' in line or 'hasattr(' in line:
                        print(f"[ERROR] {pyfile}:{i}: {line.strip()}")
                        failed = True
        return 1 if failed else 0

    def apply(self, args):
        # Solo reporta
        return self.check(args)
