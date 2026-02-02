"""
Validators for classification domain objects.

This module contains reusable validators for classification-related classes.
Any code needing to validate ClassificationRuleWrapper should import from here.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from immich_autotag.classification.classification_rule_wrapper import (
        ClassificationRuleWrapper,
    )


def validate_classification_rule(
    instance: object, attribute: Any, value: ClassificationRuleWrapper
) -> None:
    """
    Validate that value is a ClassificationRuleWrapper instance.

    This validator works with forward references by importing the type
    at validation time rather than at class definition time.

    Usage:
        from immich_autotag.classification.validators import validate_classification_rule

        @attr.s
        class MyClass:
            rule: "ClassificationRuleWrapper" = attr.ib(validator=validate_classification_rule)
    """
    from immich_autotag.classification.classification_rule_wrapper import (
        ClassificationRuleWrapper,
    )

    if not isinstance(value, ClassificationRuleWrapper):
        raise TypeError(
            f"'{attribute.name}' must be ClassificationRuleWrapper, "
            f"got {type(value).__name__}"
        )
