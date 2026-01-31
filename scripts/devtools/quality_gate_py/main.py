
import sys
import argparse
import os
from pathlib import Path
from scripts.devtools.quality_gate_py.args import QualityGateArgs
from scripts.devtools.quality_gate_py.battery import Battery
from scripts.devtools.quality_gate_py.check_black import CheckBlack
from scripts.devtools.quality_gate_py.check_isort import CheckIsort
from scripts.devtools.quality_gate_py.check_python_syntax import CheckPythonSyntax

CHECKS = {
    'check_black': CheckBlack,
    'check_isort': CheckIsort,
    'check_python_syntax': CheckPythonSyntax,
}

BATTERY_ORDER = [
    'check_python_syntax',
    'check_black',
    'check_isort',
]

def detect_venv_python():
    repo_root = Path(__file__).resolve().parent.parent.parent.parent
    venv_python = repo_root / '.venv' / 'bin' / 'python'
    if venv_python.exists():
        return str(venv_python)
    return sys.executable

def parse_args():
    parser = argparse.ArgumentParser(description="Quality Gate Python OO Edition")
    parser.add_argument('--level', '-l', default='STANDARD', choices=['STRICT', 'STANDARD', 'TARGET'])
    parser.add_argument('--mode', '-m', default='APPLY', choices=['CHECK', 'APPLY'])
    parser.add_argument('--py-bin', default=None)
    parser.add_argument('--max-line-length', type=int, default=88)
    parser.add_argument('--only-check', default='')
    parser.add_argument('target_dir', nargs='?', default='immich_autotag')
    args = parser.parse_args()
    # Detectar venv si no se pasa py-bin
    py_bin = args.py_bin if args.py_bin else detect_venv_python()
    return QualityGateArgs(
        level=args.level,
        mode=args.mode,
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
        rc = check.check(args) if args.mode == 'CHECK' else check.apply(args)
        sys.exit(rc)
    # Battery
    battery = Battery([CHECKS[name]() for name in BATTERY_ORDER])
    rc = battery.run(args.mode, args)
    sys.exit(rc)

if __name__ == '__main__':
    main()
