
from python_qualitygate.implementations.check_black import CheckBlack
from python_qualitygate.implementations.check_isort import CheckIsort
from python_qualitygate.implementations.check_python_syntax import CheckPythonSyntax
from python_qualitygate.implementations.check_ruff import CheckRuff
from python_qualitygate.implementations.check_flake8 import CheckFlake8
from python_qualitygate.implementations.check_mypy import CheckMypy
from python_qualitygate.implementations.check_shfmt import CheckShfmt
from python_qualitygate.implementations.check_no_spanish_chars import CheckNoSpanishChars
from python_qualitygate.implementations.check_jscpd import CheckJscpd
from python_qualitygate.implementations.check_no_tuples import CheckNoTuples
from python_qualitygate.implementations.check_import_linter import CheckImportLinter
from python_qualitygate.implementations.check_no_dynamic_attrs import CheckNoDynamicAttrs
from python_qualitygate.implementations.check_ssort import CheckSsort

# BATTERY_ORDER must be defined before CHECKS and validation
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

# List of all check classes (order does not matter for CHECKS, but must match BATTERY_ORDER for correctness)
CHECK_CLASSES = [
    CheckPythonSyntax,
    CheckMypy,
    CheckJscpd,
    CheckImportLinter,
    CheckNoDynamicAttrs,
    CheckNoTuples,
    CheckNoSpanishChars,
    CheckShfmt,
    CheckIsort,
    CheckSsort,
    CheckBlack,
    CheckRuff,
    CheckFlake8,
]

# Build the CHECKS map dynamically from the class 'name' property
CHECKS = {cls.name: cls for cls in CHECK_CLASSES}

# DEBUG: Print the keys of CHECKS to diagnose registry population
print("[DEBUG] CHECKS keys:", list(CHECKS.keys()))

# Validate that all BATTERY_ORDER names are present in CHECKS
missing = [name for name in BATTERY_ORDER if name not in CHECKS]
if missing:
    raise KeyError(f"Missing checks in CHECKS for BATTERY_ORDER: {missing}")
