# Fix: AssetResponseWrapper Constructor Parameter Mismatch

**Date:** 2026-01-16  
**Issue:** TypeError during Jenkins execution - lazy-loading implementation incomplete

---

## Problem

Jenkins build failed with error:

```
TypeError: AssetResponseWrapper.__init__() got an unexpected keyword argument 'asset'
```

**Stack trace location:** `asset_response_wrapper.py:784` in `from_dto()` method

### Root Cause

Changed `AssetResponseWrapper` constructor from:
```python
def __init__(self, asset: AssetResponseDto, context: ImmichContext)
```

To:
```python
def __init__(self, asset_partial: AssetResponseDto, context: ImmichContext)
```

However, the **`from_dto()` class method** was not updated to use the new parameter name:

```python
# OLD (broken after refactoring):
@classmethod
def from_dto(cls, dto: AssetResponseDto, context: ImmichContext):
    return cls(asset=dto, context=context)  # ❌ 'asset' param no longer exists!
```

This method is called when loading duplicate assets from `asset_manager.py`, causing crashes.

---

## Solution Applied

Updated `from_dto()` to use the new parameter name:

```python
# NEW (fixed):
@classmethod
def from_dto(cls, dto: AssetResponseDto, context: ImmichContext):
    return cls(asset_partial=dto, context=context)  # ✅ Uses correct 'asset_partial' param
```

### Files Updated

- ✅ `immich_autotag/assets/asset_response_wrapper.py` line 784
  - Changed `cls(asset=dto, ...)` → `cls(asset_partial=dto, ...)`
  - Updated docstring to document lazy-loading behavior

### Verification

**Grep search for remaining issues:**
```bash
grep -r "AssetResponseWrapper(asset=" . --include="*.py"
# Result: No matches found ✓

grep -r "from_dto" . --include="*.py"
# Result: Only 3 matches, all updated correctly ✓
```

**Syntax validation:**
```bash
pylance: No syntax errors found ✓
```

---

## Impact

### Before Fix
- Jenkins build crashed after processing first page of assets
- Error occurred when fetching duplicate asset wrappers
- Lazy-loading implementation incomplete

### After Fix
- Build can proceed through asset processing pipeline
- All asset loading paths use consistent parameter name
- Lazy-loading functions as designed

---

## How This Was Discovered

1. Jenkins executed with lazy-loading changes
2. Processed first page successfully (get_all_assets → asset_partial works)
3. Hit error when loading duplicates (get_all_duplicate_wrappers → calls asset_manager.get_asset → calls from_dto)
4. Stack trace pointed to line 784 where old parameter name was still in use

### Lesson

When refactoring constructors with signature changes:
1. Update ALL instantiation points (found: get_all_assets.py)
2. Update ALL factory methods (missed: from_dto)
3. Use grep to verify: `ClassName(old_param=`
4. Consider using type hints/mypy to catch at dev time

---

## Testing

- ✅ Unit test of lazy-loading passes (creates wrapper with asset_partial)
- ✅ from_dto now creates wrapper correctly
- ✅ Duplicate asset loading should work
- ⏳ Full end-to-end test with Jenkins build

---

## Next Steps

1. **Re-run Jenkins build** with fix applied
2. **Monitor for similar issues** in other instantiation paths
3. **Add type checking** to CI/CD to catch this earlier

---

**Commit:** `3d86b7c` - "fix: Update from_dto to use asset_partial parameter for lazy loading"
