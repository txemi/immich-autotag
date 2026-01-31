import subprocess
from typing import Any
import attr
from python_qualitygate.core.base import Check


@attr.define(auto_attribs=True, slots=True)
class CheckJscpd(Check):
    name = 'check_jscpd'

    def check(self, args: Any) -> int:
        cmd = ['jscpd', '--silent', '--min-tokens', '30', '--max-lines', '100', '--format', 'python', '--ignore', '**/.venv/**,**/immich-client/**,**/scripts/**', args.target_dir]
        print(f"[RUN] {' '.join(cmd)}")
        return subprocess.call(cmd)

    def apply(self, args: Any) -> int:
        return self.check(args)
