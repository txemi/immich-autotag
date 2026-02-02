# Log Level Improvement - Summary of Changes

**Date:** 2026-02-01/02  
**Branch:** `feature/stability-testing-incremental-assets`  
**Status:** ✅ Implemented and Tested

## Problems Solved

### 1. **Confusing Log Output**
   - Logs were showing `[Level 15]`, `[Level 17]` instead of readable names
   - Made it unclear what level each message represented

### 2. **Excessive Verbosity**
   - Default level for batch operations was too verbose
   - Showed too much detail per asset, overwhelming the output

### 3. **Initialization Order Issue**
   - `ImmichContext` wasn't initialized when maintenance operations needed it
   - Caused runtime errors during cleanup phase

## Solutions Applied

### 1. **Fixed Custom Log Level Registration** (logging/utils.py)
   - **Bug**: Was accessing `level.value` directly (which is a `LogLevelInfo` object)
   - **Fix**: Changed to use proper methods: `level.level_value()` and `level.is_custom()`
   - **Improvement**: Used public API `logging.getLevelNamesMapping()` instead of private `_nameToLevel`
   - **Result**: Now shows `[FOCUS]`, `[ASSET_SUMMARY]`, `[PROGRESS]` instead of numbers

### 2. **Adjusted Logging Level for Batch Operations** (logging/init.py)
   - **Changed**: Default level from `PROGRESS` (20) to `ASSET_SUMMARY` (17)
   - **Benefit**: 
     - Shows brief per-asset status (processed, skipped, error)
     - Less verbose than FOCUS (15)
     - Ideal for monitoring batch progress
   - **Behavior**: Still uses FOCUS (15) when running with asset filter (debug mode)

### 3. **Fixed Initialization Order** (entrypoints/main_logic.py)
   - **Problem**: `maintenance_cleanup_labels()` called before `init_collections_and_context()`
   - **Solution**: Moved context initialization earlier in the sequence
   - **Result**: ImmichContext now available for all operations that need it

## New Behavior

### Log Output Examples

**Before:**
```
[Level 15] Evaluating asset: id=6e9b8ae8...
[Level 17] Processing: photo.jpg
[INFO] Result: completed
```

**After:**
```
[FOCUS] Evaluating asset: id=6e9b8ae8...
[ASSET_SUMMARY] Processing: photo.jpg
[INFO] Result: completed
```

### Log Level Hierarchy (by verbosity)
1. **ERROR** (40) - Critical errors only
2. **WARNING** (30) - Important warnings
3. **PROGRESS** (20) - Progress updates, phase changes
4. **ASSET_SUMMARY** (17) - Brief per-asset status (default for batch)
5. **FOCUS** (15) - Detailed info about specific asset (when filtering)
6. **DEBUG** (10) - Very verbose details
7. **TRACE** (5) - Ultra-verbose diagnostic output

## Verification

✅ Application runs without errors  
✅ Log levels display correctly as names  
✅ Verbosity is appropriate for batch operations  
✅ ImmichContext initializes properly  
✅ Maintenance cleanup completes successfully  

## Files Modified

1. `immich_autotag/logging/utils.py` - Fixed level registration
2. `immich_autotag/logging/init.py` - Changed default level to ASSET_SUMMARY
3. `immich_autotag/entrypoints/main_logic.py` - Fixed initialization order

---

*Ready for stability testing with incremental asset volumes*

