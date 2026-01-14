# 0017 - AI Development Context

**Date**: 2026-01-14
**Status**: Proposed
**AI Model**: Claude Haiku 4.5
**Branch**: `feature/rules-tag-album-combination` (to be created)

## Problem Analysis
The user identified that the current `ClassificationRule` implementation requires separate rules for scenarios where assets need to match multiple independent criteria (tag AND album). This creates redundancy and makes configuration less expressive.

## Key Decision: AND Logic vs OR Logic
**Decision**: Use AND logic for combined criteria
- **Rationale**: More intuitive for users; "I want photos tagged as 'event' AND in date-based albums"
- **Alternative considered**: OR logic (rejected; would add complexity without clear benefit)

## Current Implementation Review
### ClassificationRule Structure (immich_autotag/config/models.py)
```python
@attrs.define
class ClassificationRule:
    tag_names: list[str] = attrs.field(factory=list)
    album_name_patterns: list[str] = attrs.field(factory=list)
```
- Currently, both fields are optional but treated as separate rules
- Matching is done via `ClassificationRuleSet.matching_rules(asset_wrapper)`

### Matching Logic (immich_autotag/assets/classification/classification_rule_set.py)
- Each rule is evaluated independently
- Returns MatchResultList with matches sorted by classification count
- Currently no support for combined matching

## Implementation Plan

### Phase 1: Update ClassificationRule
- Allow both fields to be populated simultaneously
- Add docstring clarifying AND semantics
- Add validation if needed

### Phase 2: Update Matching Logic
- Modify `ClassificationRuleSet.matching_rules()` to check both criteria when present
- Implement AND logic: asset must satisfy all specified criteria
- Handle edge cases (empty lists, partial matches)

### Phase 3: Testing & Examples
- Add unit tests for combined matching scenarios
- Update config template with examples
- Document in code comments

## Architecture Considerations
- No breaking changes required (backward compatible)
- Matching logic extension is straightforward
- No new dependencies needed
- Performance impact minimal (same number of checks)

## Example Use Case Addressed
Before: Required 2 separate rules
```python
ClassificationRule(tag_names=["event"]),
ClassificationRule(album_name_patterns=[r"^\d{4}"]),
```

After: Single expressive rule
```python
ClassificationRule(
    tag_names=["event"],
    album_name_patterns=[r"^\d{4}"]
)
```

## Potential Challenges
1. **User confusion**: Clear documentation essential to explain AND logic
2. **Config complexity**: Users might overuse combined rules; recommend keeping simple
3. **Testing complexity**: More combinations to test; use property-based testing if available

## Related Context
- Issue #0004 discusses album detection patterns
- Issue #0010 covers core tagging logic
- Issue #0009 established the config model structure
- Feature #0016 (auto-album-creation) could benefit from this eventually

## Next Steps
1. Create feature branch `feature/rules-tag-album-combination`
2. Implement Phase 1 (model changes)
3. Implement Phase 2 (matching logic)
4. Write tests for combined scenarios
5. Update documentation
6. Create pull request with examples
