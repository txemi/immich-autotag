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
        check = args.only_check()
        rc = check.check(args) if args.mode == QualityGateMode.CHECK else check.apply(args)
        sys.exit(rc)
    # Battery
    # Apply skip checks if requested via CLI `--skip-checks`.
    ordered = BATTERY_ORDER
    if getattr(args, 'skip_checks', None):
        skips = set(args.skip_checks)
        ordered = [cls for cls in BATTERY_ORDER if cls().get_name() not in skips]
    battery = Battery([cls() for cls in ordered])
    rc = battery.run(args.mode, args)
    print("")
    print("═══════════════════════════════════════════════════════════════════════════════")
    print("[REPRODUCIBLE COMMAND] To reproduce this exact execution, run:")
    print("")
    print(f"  {' '.join(sys.argv)}")
    print("")
    print("═══════════════════════════════════════════════════════════════════════════════")
    sys.exit(rc)
