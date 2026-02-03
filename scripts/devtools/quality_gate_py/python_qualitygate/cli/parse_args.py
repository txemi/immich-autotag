import argparse
from pathlib import Path
from python_qualitygate.cli.args import QualityGateArgs
from python_qualitygate.core.enums_mode import QualityGateMode
from python_qualitygate.core.enums_level import QualityGateLevel

def detect_venv_python():
    # Detect the virtual environment Python binary
    repo_root = Path(__file__).resolve().parent.parent.parent.parent
    venv_python = repo_root / '.venv' / 'bin' / 'python'
    if venv_python.exists():
        return str(venv_python)
    import sys
    return sys.executable

def parse_args():
    from python_qualitygate.batteries.registry import CHECKS
    checks_list = ', '.join(list(CHECKS.keys()))
    parser = argparse.ArgumentParser(
        description=f"Quality Gate Python OO Edition\n\nOpciones para --only-check: {checks_list}"
    )
    parser.add_argument('--level', '-l', default='STANDARD', choices=[e.value for e in QualityGateLevel])
    parser.add_argument('--mode', '-m', default='APPLY', choices=[e.value for e in QualityGateMode])
    parser.add_argument('--py-bin', default=None)
    parser.add_argument('--max-line-length', type=int, default=88)
    parser.add_argument('--only-check', default='')
    parser.add_argument('target_dir', nargs='?', default='immich_autotag')
    args = parser.parse_args()
    # Detect venv if py-bin is not provided
    py_bin = args.py_bin if args.py_bin else detect_venv_python()
    from pathlib import Path
    # Map only_check string to Check class if provided
    from python_qualitygate.batteries.registry import CHECKS
    only_check_cls = None
    if args.only_check:
        only_check_cls = CHECKS.get(args.only_check)
        if only_check_cls is None:
            valid_checks = ', '.join(list(CHECKS.keys()))
            raise ValueError(f"Unknown check: {args.only_check}. Valid options: {valid_checks}")
    return QualityGateArgs(
        level=QualityGateLevel(args.level),
        mode=QualityGateMode(args.mode),
        py_bin=py_bin,
        line_length=args.max_line_length,
        target_dir=Path(args.target_dir),
        only_check=only_check_cls,
    )
