
import sys
import argparse
import os
from pathlib import Path
from scripts.devtools.quality_gate_py.args import QualityGateArgs
from scripts.devtools.quality_gate_py.battery import Battery
from scripts.devtools.quality_gate_py.check_black import CheckBlack
from scripts.devtools.quality_gate_py.check_isort import CheckIsort
from scripts.devtools.quality_gate_py.check_python_syntax import CheckPythonSyntax
from scripts.devtools.quality_gate_py.check_ruff import CheckRuff
from scripts.devtools.quality_gate_py.check_flake8 import CheckFlake8
from scripts.devtools.quality_gate_py.check_mypy import CheckMypy
from scripts.devtools.quality_gate_py.check_shfmt import CheckShfmt
from scripts.devtools.quality_gate_py.check_no_spanish_chars import CheckNoSpanishChars
from scripts.devtools.quality_gate_py.check_jscpd import CheckJscpd
from scripts.devtools.quality_gate_py.check_no_tuples import CheckNoTuples
from scripts.devtools.quality_gate_py.check_import_linter import CheckImportLinter
from scripts.devtools.quality_gate_py.check_no_dynamic_attrs import CheckNoDynamicAttrs
from scripts.devtools.quality_gate_py.check_ssort import CheckSsort
from scripts.devtools.quality_gate_py.enums_mode import QualityGateMode
from scripts.devtools.quality_gate_py.enums_level import QualityGateLevel

CHECKS = {
    'check_black': CheckBlack,
    'check_isort': CheckIsort,
    'check_python_syntax': CheckPythonSyntax,
    'check_ruff': CheckRuff,
    'check_flake8': CheckFlake8,
    'check_mypy': CheckMypy,
    'check_shfmt': CheckShfmt,
    'check_no_spanish_chars': CheckNoSpanishChars,
    'check_jscpd': CheckJscpd,
    'check_no_tuples': CheckNoTuples,
    'check_import_linter': CheckImportLinter,
    'check_no_dynamic_attrs': CheckNoDynamicAttrs,
    'check_ssort': CheckSsort,
}

BATTERY_ORDER = [
    'check_python_syntax',
    'check_mypy',
    'check_jscpd',
    'check_import_linter',
    'check_no_dynamic_attrs',
    'check_no_tuples',
    'check_no_spanish_chars',
    'check_shfmt',
    'check_isort',
    'check_ssort',
    'check_black',
    'check_ruff',
    'check_flake8',
]

def detect_venv_python():
    # Detect the virtual environment Python binary
    repo_root = Path(__file__).resolve().parent.parent.parent.parent
    venv_python = repo_root / '.venv' / 'bin' / 'python'
    if venv_python.exists():
        return str(venv_python)
    return sys.executable

def parse_args():
    parser = argparse.ArgumentParser(description="Quality Gate Python OO Edition")
    parser.add_argument('--level', '-l', default='STANDARD', choices=[e.value for e in QualityGateLevel])
    parser.add_argument('--mode', '-m', default='APPLY', choices=[e.value for e in QualityGateMode])
    parser.add_argument('--py-bin', default=None)
    parser.add_argument('--max-line-length', type=int, default=88)
    parser.add_argument('--only-check', default='')
    parser.add_argument('target_dir', nargs='?', default='immich_autotag')
    args = parser.parse_args()
    # Detect venv if py-bin is not provided
    py_bin = args.py_bin if args.py_bin else detect_venv_python()
    return QualityGateArgs(
        level=QualityGateLevel(args.level),
        mode=QualityGateMode(args.mode),
        py_bin=py_bin,
        max_line_length=args.max_line_length,
        target_dir=args.target_dir,
        only_check=args.only_check,
    )

def main():
    args = parse_args()
    print(f"[INFO] Usando Python: {args.py_bin}")
    if args.only_check:
        check_cls = CHECKS.get(args.only_check)
        if not check_cls:
            print(f"[DEFENSIVE-FAIL] Unknown check: {args.only_check}", file=sys.stderr)
            sys.exit(90)
        check = check_cls()
        rc = check.check(args) if args.mode == QualityGateMode.CHECK else check.apply(args)
        sys.exit(rc)
    # Battery
    battery = Battery([CHECKS[name]() for name in BATTERY_ORDER])
    rc = battery.run(args.mode, args)
    sys.exit(rc)

if __name__ == '__main__':
    main()
