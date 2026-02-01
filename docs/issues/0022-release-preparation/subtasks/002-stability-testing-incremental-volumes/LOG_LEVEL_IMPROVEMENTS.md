# Log Level Improvement - Summary of Changes

**Date:** 2026-02-01  
**Branch:** `feature/stability-testing-incremental-assets`

## Problem

During batch testing runs without asset filters, logs were showing `[Level 15]` which was confusing and verbose:
- The numeric level name `[Level 15]` wasn't immediately clear (it's FOCUS)
- The verbosity level was too high for batch operations (showing too much detail per asset)

## Solution Applied

### 1. Improved Log Format (logging/utils.py)
- Ensured custom log levels are registered **before** `basicConfig()` is called
- This makes the output show `[FOCUS]`, `[ASSET_SUMMARY]`, etc. instead of `[Level 15]`, `[Level 17]`
- Much more readable and self-documenting

### 2. Adjusted Logging Level for Batch Runs (logging/init.py)
- Changed default level from `LogLevel.PROGRESS` (20) to `LogLevel.ASSET_SUMMARY` (17)
- **ASSET_SUMMARY** is specifically designed for batch operations:
  - Shows a brief per-asset status (processed, skipped, error)
  - Less verbose than FOCUS (15)
  - More informative than bare PROGRESS
  - Ideal for monitoring batch progress without overwhelming output

## New Behavior

### With Filter (debug single asset):
- Level: **FOCUS** (15) - Detailed info about that specific asset

### Without Filter (batch processing):
- Level: **ASSET_SUMMARY** (17) - Brief status per asset, no excessive detail

### Example Output After Changes:
```
[ASSET_SUMMARY] Processed asset: id=6e9b8ae8... name=photo.jpg
[ASSET_SUMMARY] Applied 2 tags: [tag1, tag2]
[ASSET_SUMMARY] Next: 5/100 assets...
```

Instead of:
```
[Level 17] Processed asset: id=6e9b8ae8... name=photo.jpg
[Level 15] Evaluating rule: ClassificationRuleWrapper(...)
[Level 15] Tag applied: tag1
...
```

## Testing

Run the application normally (without asset filter) to see the improved logging:
```bash
bash run_app.sh
```

The output should now be:
- Clearer (named levels instead of numbers)
- Less overwhelming (ASSET_SUMMARY instead of FOCUS/DEBUG verbosity)
- Better for monitoring large batches

---

*Changes made to prepare for stability testing with incremental asset volumes*
