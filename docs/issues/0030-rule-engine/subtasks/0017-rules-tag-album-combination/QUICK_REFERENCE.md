# Quick Reference: Issue #0017 - Tag + Album Rules

## 🎯 The Problem
Rules can only specify **tags** OR **albums**, not both. This creates redundant rules for complex scenarios.

**Before (workaround - two separate rules):**
```python
ClassificationRule(tag_names=["event"]),
ClassificationRule(album_name_patterns=[r"^\d{4}"])
```

## ✨ The Solution
Allow both specifications in a **single rule** with **AND logic**.

**After (one expressive rule):**
```python
ClassificationRule(
    tag_names=["event", "processed"],  # Asset must have ALL these tags
    album_name_patterns=[
        r"^\d{4}-\d{2}-\d{2}",         # AND be in album matching date
        r"^Events/"                     # OR album starting with "Events/"
    ]
)
```

## 🔀 AND Logic Explained
An asset matches if:
- ✅ It has ALL specified tags: `event` AND `processed`
- ✅ AND it's in album matching ANY pattern: `2025-01-14*` OR `Events/*`

**Match Examples:**
- Asset with tags `["event", "processed"]` in album `"2025-01-14-Birthday"` → ✅ MATCH
- Asset with tag `["event"]` in album `"2025-01-14-Birthday"` → ❌ NO MATCH (missing tag)
- Asset with tags `["event", "processed"]` in album `"Random"` → ❌ NO MATCH (no pattern match)

## 🔄 Backward Compatibility
**Tag-only rules** still work:
```python
ClassificationRule(tag_names=["archived"])  # No album requirement
```

**Album-only rules** still work:
```python
ClassificationRule(album_name_patterns=[r"^\d{4}"])  # No tag requirement
```

## 📝 Files to Modify

| File | Change |
|------|--------|
| `immich_autotag/config/models.py` | Allow both fields in `ClassificationRule` |
| `immich_autotag/assets/classification/classification_rule_set.py` | Update `matching_rules()` for AND logic |
| `immich_autotag_user_config_template.py` | Add combined rule examples |
| Tests | Add test cases for tag+album scenarios |

## 🧪 Test Scenarios

```python
# Test 1: Combined tag + album (both specified)
rule = ClassificationRule(
    tag_names=["event"],
    album_name_patterns=[r"^\d{4}"]
)
# Should match: asset with "event" tag in "2025-01-14" album
# Should NOT match: asset with "event" but album "Random"

# Test 2: Tag only (backward compat)
rule = ClassificationRule(tag_names=["archived"])
# Should match: any asset with "archived" tag

# Test 3: Album only (backward compat)
rule = ClassificationRule(album_name_patterns=[r"^\d{4}"])
# Should match: any asset in date-named album
```

## 🚀 Implementation Checklist

- [ ] Update `ClassificationRule` dataclass docstring with AND logic explanation
- [ ] Implement matching logic that evaluates both criteria
- [ ] Add unit tests for combined scenarios
- [ ] Add unit tests for backward compatibility
- [ ] Update config template with examples
- [ ] Add code comments explaining AND semantics
- [ ] Verify no performance degradation
- [ ] Update project documentation
- [ ] Create PR with clear explanation

## 📚 Related Documentation

- `docs/issues/0017-rules-tag-album-combination/readme.md` - Full specification
- `docs/issues/0017-rules-tag-album-combination/ai-context.md` - Development notes
- `docs/issues/0017-rules-tag-album-combination/design/technical_design.md` - Technical details
- `docs/ISSUE_SYSTEM_CONVENTION.md` - Issue management system

## 🔗 Related Issues

- **#0004**: Album detection (existing album logic to extend)
- **#0010**: Core tagging system (existing tag logic to extend)
- **#0009**: Configuration system (config model used here)

## 💡 Future Possibilities

Once this is done, we could:
- Support OR logic for tags (any tag, not all)
- Support negative criteria ("NOT tagged as...")
- Support tag/album hierarchies more naturally
- Build complex filtering queries

---
**Status**: Proposed
**Branch**: `feature/rules-tag-album-combination`
**Created**: 2026-01-14
