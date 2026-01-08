from typing import Any, Optional

import attrs

from ._classification_tag_comparison_result import _ClassificationTagComparisonResult


@attrs.define(auto_attribs=True, slots=True, frozen=True)
class _ClassificationTagComparisonResultObj:
    result: _ClassificationTagComparisonResult
    tag_info: Optional[Any] = None
