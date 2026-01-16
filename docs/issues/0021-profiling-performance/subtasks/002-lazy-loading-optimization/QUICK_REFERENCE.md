# Quick Reference: Lazy-Loading Implementation Summary

## The Change in 30 Seconds

**Problem:** App called `get_asset_info()` for ALL 26,562 assets immediately, even if tags weren't needed.

**Solution:** Modified `AssetResponseWrapper` to defer `get_asset_info()` until tags are actually accessed.

**Impact:** Expected 5-15% improvement (50-280 seconds saved).

---

## What Changed

### 1. AssetResponseWrapper Field Structure
```python
# BEFORE
asset: AssetResponseDto  # Always fully loaded

# AFTER
asset_partial: AssetResponseDto  # From search (fast)
_asset_full: AssetResponseDto | None  # Loaded only when needed
```

### 2. Data Flow
```
BEFORE: search_assets → get_asset_info (35,402 calls) → process
AFTER:  search_assets → wrapper → (lazy) get_asset_info only if tags accessed
```

### 3. Code Usage (Same as Before!)
```python
wrapper.asset.tags  # Auto-loads if needed
wrapper.tags        # Auto-loads if needed
wrapper.has_tag()   # Auto-loads if needed
```

---

## Files Modified

| File | Change | Lines |
|------|--------|-------|
| `asset_response_wrapper.py` | Dual DTO + lazy props | +50 |
| `get_all_assets.py` | Remove immediate call | -5 |

**Total: 1 small refactor, 2 files, 100% backward compatible**

---

## Performance Baseline

| Metric | Value |
|--------|-------|
| Current execution time | 3,427.55s (57 min) |
| get_asset_info calls | 35,402 |
| Time per call | 36.73ms |
| get_asset_info time | 1,301.69s (38%) |
| Socket I/O time | 2,869s (83.7%) |

**Expected savings:** 50-280s (3-8% improvement)

---

## Testing

✅ Lazy-loading works correctly (verified with unit tests)  
✅ All existing code compatible (no changes needed)  
✅ Properties auto-load transparently  

---

## Jenkins Status

- Deployed: 2026-01-16
- Branch: `perf/symmetric-rules-with-performance`
- Expected results: profile(1).stats from build artifacts
- Validation: Compare get_asset_info call count

---

## Why Only 5-15% Improvement?

1. **Socket I/O dominates** (83.7% of time) → not affected by code optimization
2. **Most assets need tags** → ~90% still access them during classification
3. **Network latency** → CPU efficiency gains have limited impact

**This is a NETWORK problem, not a CPU problem.**

---

## What About Parallel Workers (--workers)?

❌ **Tried before, didn't work** because:
- Immich API throttles concurrent requests (429 errors)
- Database contention on Immich side
- Python GIL limits threading benefits
- Shared state requires locking

See `PARALLEL_ANALYSIS.md` for detailed breakdown.

---

## Next Optimization Phase

After validation, investigate (priority order):
1. **Batch API operations** (tag_assets in bulk) → ~142s (4.1%)
2. **Album name caching** (942k repeated queries) → ~2s (0.1%)
3. **Connection pooling tuning** → ~200s (5-10%)
4. **Async/await refactoring** → ~1,200s (40%+ but high effort)

See `OPTIMIZATION_ROADMAP.md` for details.

---

## Commands to Check Progress

```bash
# Monitor Jenkins build
curl -s https://jenkins-url/job/immich-autotag/.../api/json | jq .

# Extract profile when ready
unzip profile.stats.zip  # From build artifacts

# Check get_asset_info calls
python -m pstats profile.stats
> sort cumulative
> stats get_asset_info
> quit
```

---

## Contact & Questions

**Implementation:** ✅ Complete  
**Validation:** ⏳ In Progress (waiting for Jenkins)  
**Status:** Ready for profiling results  

**Decision Point:** Once Jenkins completes, decide whether to:
- ✓ Merge to main (if 5%+ improvement)
- ? Investigate batching (if < 5% improvement)
- ? Pivot to async/await (if < 2% improvement)

---

*Last updated: 2026-01-16*
