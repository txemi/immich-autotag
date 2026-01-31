import sys
from python_qualitygate.cli.args import QualityGateArgs
from python_qualitygate.batteries.battery import Battery
from python_qualitygate.batteries.registry import CHECKS, BATTERY_ORDER
from python_qualitygate.core.enums_mode import QualityGateMode
from python_qualitygate.core.enums_level import QualityGateLevel
from python_qualitygate.cli.parse_args import parse_args

def run_quality_gate():
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
    battery = Battery([cls() for cls in BATTERY_ORDER])
    rc = battery.run(args.mode, args)
    sys.exit(rc)
