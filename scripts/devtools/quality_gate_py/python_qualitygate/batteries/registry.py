
from python_qualitygate.implementations.check_black import CheckBlack
from python_qualitygate.implementations.check_isort import CheckIsort
from python_qualitygate.implementations.check_python_syntax import CheckPythonSyntax
from python_qualitygate.implementations.check_ruff import CheckRuff
from python_qualitygate.implementations.check_flake8 import CheckFlake8
from python_qualitygate.implementations.check_mypy import CheckMypy
from python_qualitygate.implementations.check_shfmt import CheckShfmt
from scripts.devtools.quality_gate_py.python_qualitygate.implementations.spanish_check.check_no_spanish_chars import CheckNoSpanishChars
from python_qualitygate.implementations.check_jscpd import CheckJscpd
from python_qualitygate.implementations.check_no_tuples import CheckNoTuples

from python_qualitygate.implementations.check_import_linter import CheckImportLinter
from python_qualitygate.implementations.check_large_files import CheckLargeFiles

from python_qualitygate.implementations.check_no_dynamic_attrs import CheckNoDynamicAttrs
from python_qualitygate.implementations.check_ssort import CheckSsort
from python_qualitygate.implementations.check_pylint_protected_access import CheckPylintProtectedAccess



# BATTERY_ORDER: Detailed justification for the order
#
# 1. CheckPythonSyntax: Detects critical syntax errors before any further analysis.
# 2. CheckNoSpanishChars: Detects forbidden characters and words before formatting or analysis.
# 3. CheckMypy: Static typing is fundamental to catch logical errors before code modification.
# 4. CheckImportLinter: Architecture/import rules to ensure structure before formatting.
# 5. CheckNoTuples: Design rules to avoid forbidden patterns before code modification.
# 6. CheckNoDynamicAttrs: Detects forbidden dynamic attributes, important for robustness before formatting.
# 7. CheckShfmt: Formats shell scripts, must run before linters to avoid false positives.
# 8. CheckIsort: Sorts imports, must run before linters and Python formatters.
# 9. CheckSsort: Sorts structures, if applicable, before general formatting.
# 10. CheckBlack: Formats Python, must run before linters to avoid false positives.
# 11. CheckRuff: Modern linter, fast, detects style issues after formatting.
# 12. CheckFlake8: Traditional linter, may overlap with Ruff, but adds extra rules.
# 13. CheckPylintProtectedAccess: Specific protected access rules, after formatting and general linters.
# 14. CheckJscpd: Duplicate detection, expensive, best at the end to avoid blocking the flow.
# 15. CheckLargeFiles: Large file detection, expensive, best at the end.

BATTERY_ORDER = [
    CheckPythonSyntax,           # Syntax first: blocks everything else if it fails
    CheckNoSpanishChars,         # Forbidden chars/words before code modification
    CheckMypy,                   # Typing before formatting to catch logical errors
    CheckImportLinter,           # Architecture/imports before formatting
    CheckNoTuples,               # Design rules before code modification
    CheckNoDynamicAttrs,         # Robustness before formatting
    CheckShfmt,                  # Shell formatting before linters
    CheckIsort,                  # Import sorting before linters
    CheckSsort,                  # Structure sorting before general formatting
    CheckBlack,                  # Python formatting before linters
    CheckRuff,                   # Modern linter after formatting
    CheckFlake8,                 # Traditional linter after formatting
    CheckPylintProtectedAccess,  # Specific rules after general linters
    CheckJscpd,                  # Duplicate detection at the end, expensive
    CheckLargeFiles,             # Large file detection at the end, expensive
]



# CHECKS map for lookup by name, using get_name() from an instance
from typing import Dict, Type
CHECKS: Dict[str, type] = {cls().get_name(): cls for cls in BATTERY_ORDER}

# No need for validation: BATTERY_ORDER is the single source of truth for order and membership
