
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




# BATTERY_ORDER: Each module is justified inline for its position relative to the next.
BATTERY_ORDER = [
    CheckPythonSyntax,           # Must be first: syntax errors block all further checks. Only after syntax is valid can forbidden chars/words be reliably detected.
    CheckNoSpanishChars,         # Forbidden chars/words must be removed before static typing, since they may cause mypy to fail or misinterpret code.
    CheckMypy,                   # Static typing (mypy) should run before architectural checks, as type errors are more fundamental and may block import structure analysis.
    CheckImportLinter,           # Import structure must be validated before design rules (like tuple usage), since architectural violations are more critical.
    CheckNoTuples,               # Tuple usage is a design constraint; dynamic attribute checks depend on code structure being valid and tuple rules enforced.
    CheckNoDynamicAttrs,         # Dynamic attribute checks ensure robustness before formatting shell scripts, as shell formatting does not affect Python robustness.
    CheckShfmt,                  # Shell formatting must precede import sorting, since shell scripts are independent and should be formatted before Python-specific checks.
    CheckIsort,                  # Import sorting (isort) should run before structure sorting (ssort), as imports are a distinct structure and must be ordered first.
    CheckSsort,                  # Structure sorting (ssort) should run before general Python formatting (black), since ssort may change code blocks that black will then format.
    CheckBlack,                  # Python formatting (black) must run before modern linters (ruff), to avoid false positives and ensure code is well-formatted for linting.
    CheckRuff,                   # Ruff (modern linter) runs before Flake8 (traditional linter), as Ruff is faster and covers more cases; Flake8 adds extra rules after Ruff.
    CheckFlake8,                 # Flake8 runs before PylintProtectedAccess, since general linting should precede specific protected access checks.
    CheckPylintProtectedAccess,  # Protected access checks should run before duplicate detection (jscpd), as jscpd is expensive and should only run after all code is clean.
    CheckJscpd,                  # Duplicate detection (jscpd) runs before large file detection, since jscpd is more likely to block the pipeline; large file checks are last and most expensive.
    CheckLargeFiles,             # Large file detection is last, most expensive, and should only run after all other checks pass.
]



# CHECKS map for lookup by name, using get_name() from an instance
from typing import Dict, Type
CHECKS: Dict[str, type] = {cls().get_name(): cls for cls in BATTERY_ORDER}

# No need for validation: BATTERY_ORDER is the single source of truth for order and membership
