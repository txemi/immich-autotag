# 0017 - AI Development Context

**Date**: 2026-01-14
**Status**: Proposed
**AI Model**: Claude Haiku 4.5
**Branch**: `feature/rules-tag-album-combination` (to be created)

## Problem Analysis
The user identified that the current `ClassificationRule` implementation requires separate rules for scenarios where assets need to match multiple independent criteria (tag AND album). This creates redundancy and makes configuration less expressive.

## Key Decision: OR Logic (Unified Rule Concept)
**Decision**: Use OR logic for combined criteria - a rule matches if ANY of its conditions are met
- **Rationale**: A `ClassificationRule` is now an abstract concept that represents a classification category. An asset belongs to that category if it matches ANY of the specified criteria (tags OR album patterns).
- **Conceptual Shift**: Previously, we treated tags and albums as separate matching systems. Now, a rule is a unified concept - it either matches or doesn't match as a whole unit.
- **Example**: `ClassificationRule(tag_names=["meme", "autotag_input_meme"], album_name_patterns=[r"^autotag_input_meme$"])` means "this asset is a meme if it has those tags OR is in an album with that name"
- **Alternative considered**: AND logic (rejected; would be too restrictive and doesn't match the conceptual model of classification categories)

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
- Modify `ClassificationRuleWrapper.matches()` to check both criteria when present
- Implement OR logic: asset matches if it satisfies ANY specified criteria (tags OR albums)
- The rule is evaluated as a single unit - it either matches or doesn't
- Remove the restriction that prevented having both tag_names and album_name_patterns

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
Before: Only one criterion per rule
```python
ClassificationRule(tag_names=["meme", "autotag_input_meme"]),
# OR in a separate rule:
ClassificationRule(album_name_patterns=[r"^autotag_input_meme$"]),
```

After: Single unified rule with OR logic
```python
ClassificationRule(
    tag_names=["meme", "autotag_input_meme"],
    album_name_patterns=[r"^autotag_input_meme$"]
)
# Matches if the asset has those tags OR is in an album matching that pattern
```
## Potential Challenges
1. **User confusion**: Clear documentation essential to explain OR logic
2. **Legacy code assumptions**: Some code sections assumed tags and albums were separate systems
3. **Testing complexity**: More combinations to test; ensure OR logic works correctly
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
