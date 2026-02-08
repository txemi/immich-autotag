
import attr
from python_qualitygate.cli.args import QualityGateArgs
from python_qualitygate.core.base import Check
from python_qualitygate.core.result import QualityGateResult
from scripts.devtools.quality_gate_py.python_qualitygate.implementations.common_qualitygate import run_subprocess_and_process

@attr.define(auto_attribs=True, slots=True)
class CheckBlack(Check):
    _name: str = attr.ib(default='check_black', init=False)

    def get_name(self) -> str:
        return self._name

    def check(self, args: QualityGateArgs) -> QualityGateResult:
        cmd = [args.py_bin, '-m', 'black', '--check', '--line-length', str(args.line_length), str(args.target_dir)]
        def process_line(line):
            if line.strip().endswith('would reformat'):
                file_path = line.split()[0]
                return Finding(file_path=file_path, line_number=0, message="File not formatted with black", code="black-format")
            return None
        return run_subprocess_and_process(cmd, process_line, error_code=1, target_dir=args.target_dir, code="black-format")

    def apply(self, args: QualityGateArgs) -> QualityGateResult:
        cmd = [args.py_bin, '-m', 'black', '--line-length', str(args.line_length), str(args.target_dir)]
        def process_line(line):
            if line.strip().endswith('would reformat'):
                file_path = line.split()[0]
                return Finding(file_path=file_path, line_number=0, message="File not formatted with black", code="black-format")
            return None
        return run_subprocess_and_process(cmd, process_line, error_code=1, target_dir=args.target_dir, code="black-format")
