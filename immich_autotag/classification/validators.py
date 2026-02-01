"""
Validators for classification domain objects.

This module contains reusable validators for classification-related classes.
Any code needing to validate ClassificationRuleWrapper should import from here.
"""

import attr


def validate_classification_rule(
    instance: object, attribute: attr.Attribute, value: object
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
