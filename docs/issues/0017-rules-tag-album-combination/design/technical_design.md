# Technical Design: Combined Tag + Album Rule Matching

## Overview
This document describes the technical design for allowing `ClassificationRule` to specify both tag and album criteria simultaneously with AND logic.

## Data Model Changes

### Current ClassificationRule (immich_autotag/config/models.py)
```python
@attrs.define
class ClassificationRule:
    tag_names: list[str] = attrs.field(factory=list, validator=deep_iterable(...))
    album_name_patterns: list[str] = attrs.field(factory=list, validator=deep_iterable(...))
```

### No changes needed to dataclass
The model already supports both fields. The interpretation logic needs updating.

## Matching Logic Changes

### File: immich_autotag/assets/classification/classification_rule_set.py
**Current behavior**: Iterate rules, check tags OR albums separately

**New behavior**: For each rule:
1. If `tag_names` is empty → no tag requirement
2. If `album_name_patterns` is empty → no album requirement
3. If both are populated → asset must satisfy BOTH (AND logic)
4. If neither → rule never matches (should not occur in practice)

### Pseudo-code
```python
def _rule_matches_asset(rule: ClassificationRule, asset_wrapper: AssetResponseWrapper) -> bool:
    # Check tag criteria
    if rule.tag_names:
        asset_tags = {tag.name for tag in asset_wrapper.tags}
        if not all(tag_name in asset_tags for tag_name in rule.tag_names):
            return False  # Asset doesn't have all required tags
    
    # Check album criteria
    if rule.album_name_patterns:
        asset_album_names = {album.name for album in asset_wrapper.albums}
        pattern_matches = any(
            any(re.match(pattern, album_name) for pattern in rule.album_name_patterns)
            for album_name in asset_album_names
        )
        if not pattern_matches:
            return False  # Asset not in any matching album
    
    # Both criteria satisfied (or no criteria specified)
    return True
```

## Example Scenarios

### Scenario 1: Tag-only rule (backward compatible)
```python
ClassificationRule(tag_names=["archived"])
```
- Matches: Any asset with tag "archived"
- No album requirement

### Scenario 2: Album-only rule (backward compatible)
```python
ClassificationRule(album_name_patterns=[r"^2024"])
```
- Matches: Any asset in album starting with "2024"
- No tag requirement

### Scenario 3: Combined tag + album rule (new)
```python
ClassificationRule(
    tag_names=["event", "processed"],
    album_name_patterns=[r"^\d{4}-\d{2}-\d{2}", r"^Events/"]
)
```
- Matches: Asset that:
  - Has BOTH tags "event" AND "processed"
  - AND is in an album matching either pattern

### Scenario 4: Combined with multiple tags
```python
ClassificationRule(
    tag_names=["location_france", "family"],
    album_name_patterns=[r"^France/", r"^Family-"]
)
```
- Matches: Asset with both "location_france" AND "family"
- AND in album "France/..." OR "Family-..."

## Integration Points

### 1. ClassificationRuleSet.matching_rules()
```python
def matching_rules(self, asset_wrapper: AssetResponseWrapper) -> MatchResultList:
    """Returns rules that match the asset, sorted by classification count."""
    results = []
    for rule in self.rules:
        if self._rule_matches_asset(rule, asset_wrapper):
            count = len(rule.tag_names) + len(rule.album_name_patterns)
            results.append(MatchResult(rule=rule, classification_count=count))
    
    return MatchResultList(
        results=sorted(results, key=lambda x: x.classification_count)
    )
```

### 2. Configuration Loading
No changes needed; model already supports both fields.

### 3. Validation
Consider adding validation to ensure rules are meaningful:
- Warn if rule has no criteria (both lists empty)
- Suggest simplification if rules are obviously redundant

## Backward Compatibility
✅ All existing rules continue to work:
- Rules with only tags: tag criterion checked, album criterion skipped
- Rules with only albums: album criterion checked, tag criterion skipped
- Both scenarios are supported by AND logic naturally

## Testing Strategy

### Unit Tests (immich_autotag/tests/test_classification_rule_set.py)
```python
def test_combined_tag_album_rule_matches():
    """Asset with tags AND in matching album."""

def test_combined_tag_album_rule_missing_tag():
    """Asset missing one tag → no match."""

def test_combined_tag_album_rule_wrong_album():
    """Asset has tags but wrong album → no match."""

def test_combined_tag_album_rule_partial_tags():
    """Asset has some but not all tags → no match."""

def test_backward_compatibility_tag_only():
    """Existing tag-only rule still works."""

def test_backward_compatibility_album_only():
    """Existing album-only rule still works."""
```

### Integration Test
Test with actual config containing combined rules.

## Performance Considerations
- Matching logic: O(n*m) where n = criteria count, m = asset attributes
- For typical configs: negligible impact
- No new database queries or API calls

## Edge Cases

### 1. Empty rule (both lists empty)
- Currently: Would never match
- Recommendation: Add validation/warning in config loading

### 2. Asset with no tags
- Tag criterion: Not satisfied if tags are required
- Works correctly with AND logic

### 3. Asset with no albums
- Album criterion: Not satisfied if patterns are required
- Works correctly with AND logic

### 4. Overlapping rules
- If multiple rules match, classification follows existing logic
- No change in behavior

## Documentation Requirements

### User-Facing (user_config_template.py)
Add example:
```python
# Combined tag + album classification: events in date-based albums
ClassificationRule(
    tag_names=["event"],
    album_name_patterns=[r"^\d{4}-\d{2}-\d{2}"]
),
```

### Code Comments
Clarify AND logic in matching functions.

## Rollout Plan
1. Implement model interpretation (no breaking changes)
2. Add comprehensive tests
3. Update examples
4. Release as patch/minor version (backward compatible)
5. Update documentation and announcements
