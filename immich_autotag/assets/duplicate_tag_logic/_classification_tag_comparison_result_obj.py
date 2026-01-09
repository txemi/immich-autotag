from typing import Any, Optional

import attrs

from ._classification_tag_comparison_result import ClassificationTagComparisonResult


@attrs.define(auto_attribs=True, slots=True, frozen=True)
class ClassificationTagComparisonResultObj:
    result: ClassificationTagComparisonResult
    tag_info: Optional[Any] = None
