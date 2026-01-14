---
status: Proposed
version: v1.0
created: 2026-01-14
updated: 2026-01-14
---

# 0017 - Allow Classification Rules to Specify Both Tag and Album Patterns

**Tech Stack:** #Python #Configuration #Rules #Classification #Tags #Albums

## Context
Currently, `ClassificationRule` can specify **either** a set of `tag_names` **or** a set of `album_name_patterns`, but not both simultaneously in a single rule. This limitation forces users to create multiple rules for assets that should be classified by a combination of tag AND album criteria.

## Problem Statement
Use cases requiring combined tag + album matching:
- "Assets tagged with 'event' that are in albums matching date pattern (YYYY-MM-DD)"
- "Photos tagged with 'location_family' in albums starting with 'Family-'"
- "Videos tagged with 'archive' in albums named 'Archive-*'"

Current workaround: Users must create separate rules, losing the semantic grouping of related criteria.

## Proposed Solution
Allow `ClassificationRule` to specify both `tag_names` AND `album_name_patterns` simultaneously:
- An asset must match **ALL** specified criteria (AND logic, not OR)
- If `tag_names` is empty, no tag matching is required
- If `album_name_patterns` is empty, no album pattern matching is required
- If both are specified, the asset must have ALL tags AND be in an album matching ANY pattern

### Example Configuration
```python
ClassificationRule(
    tag_names=["event", "archived"],  # Asset must have both tags
    album_name_patterns=[
        r"^\d{4}-(\d{2}(-\d{2})?)?",   # Album must match date pattern
        r"^Events/"                     # OR album starts with "Events/"
    ]
)
```

## Definition of Done (DoD)
- [ ] `ClassificationRule` accepts both `tag_names` and `album_name_patterns` in a single rule
- [ ] Matching logic updated in `ClassificationRuleSet.matching_rules()` to handle combined criteria
- [ ] AND logic correctly applied: asset must satisfy ALL specified criteria
- [ ] Unit tests for combined matching (tag+album, tag-only, album-only)
- [ ] Configuration examples updated in `user_config_template.py`
- [ ] Documentation updated explaining AND logic for combined rules
- [ ] Backward compatible: existing single-criteria rules continue to work
- [ ] No performance degradation from matching logic changes
- [ ] Logging clarifies when rules are matched (shows both tag and album matches)

## Implementation Strategy

### 1. Core Changes
- **File**: `immich_autotag/config/models.py`
  - Modify `ClassificationRule` dataclass to allow both fields to be non-empty
  - Update validation logic to clarify AND semantics
  
### 2. Matching Logic
- **File**: `immich_autotag/assets/classification/classification_rule_set.py`
  - Update `matching_rules()` method to evaluate combined criteria
  - Ensure AND logic: `(tag_match) AND (album_match)`
  - Handle edge cases: empty lists, partial matches

### 3. Testing
- **File**: `tests/test_classification_rule_set.py` (or similar)
  - Test combined tag+album matching
  - Test backward compatibility with single-criterion rules
  - Test AND logic thoroughly

### 4. Documentation
- Update `user_config_template.py` with examples
- Update CONTRIBUTING.md or development guides if needed
- Add inline code comments explaining AND logic

## Entry Points
- **Primary**: `immich_autotag/config/models.py` → `ClassificationRule`
- **Secondary**: `immich_autotag/assets/classification/classification_rule_set.py` → `matching_rules()`

## Acceptance Criteria
1. A `ClassificationRule` can specify both `tag_names` and `album_name_patterns`
2. Asset matching requires ALL conditions to be true (AND logic)
3. Backward compatibility maintained for existing rules
4. Configuration examples demonstrate combined rule usage
5. Code is type-checked and follows project style

## Related Issues
- #0004: Album detection (existing album detection logic to extend)
- #0010: Core tagging system (existing tag matching logic to extend)
- #0009: Configuration system refactor (config model used here)

## Notes
- This enables more sophisticated classification scenarios without rule explosion
- Users can express complex business logic more naturally in configuration
- Foundation for future filtering by multiple criteria

## References
- See `design/` folder for technical details
- See `ai-context.md` for development context and decision history
