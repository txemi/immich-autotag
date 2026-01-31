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
