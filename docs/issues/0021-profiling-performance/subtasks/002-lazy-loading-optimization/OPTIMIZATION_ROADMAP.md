# Optimization Roadmap: Socket I/O & API Bottleneck Resolution

**Status:** Strategic Planning  
**Created:** 2026-01-16  
**Target Phase:** Post lazy-loading validation  

---

## Current Bottleneck (After Lazy-Loading)

After lazy-loading optimization, the bottleneck **will remain Socket I/O**:
- **Socket recv()**: ~2,869 seconds (83.7% of execution)
- **API calls**: ~43,892 (reduced from initial 43,892 with lazy-loading savings)

To get significant improvement, we **must address the I/O bottleneck**.

---

## Optimization Opportunities (Priority Order)

### 🥇 **Priority 1: Batch API Operations** (Highest ROI)

#### Opportunity: Tag Operations Batching

**Current State:**
```
2,479 tag_assets calls (add tags)
1,418 untag_assets calls (remove tags)
= 3,897 individual API calls for tag operations
```

**Investigation Required:**
1. Check if Immich API supports batch tagging:
   ```
   POST /api/assets/bulk/update
   { "tag_ids": [1,2,3], "asset_ids": [aid1, aid2, aid3] }
   ```
2. If supported: Batch 100 assets per call → ~40 calls instead of 3,897
3. Expected savings: 3,857 API calls × 36.73ms = **142 seconds (4.1%)**

**Implementation Effort:** Medium (API investigation + batching logic)

**Files to Investigate:**
- `immich-client/immich_client/api/tags/tag_assets.py`
- `immich_autotag/assets/process_single_asset.py`

---

#### Opportunity: Search Results Consolidation

**Current State:**
- `search_assets()`: 107 calls (one per page)
- `get_album_info()`: 3,377 calls (fetched individually)

**Investigation Required:**
1. Verify pagination: Do we need 107 pages or can we fetch all in fewer requests?
2. Album batching: Can we fetch multiple albums in one call?
3. Potential savings: 10-20% reduction in search/album operations

**Implementation Effort:** Low (config/parameter tuning)

---

### 🥈 **Priority 2: Album Name Caching** (High Volume)

**Current State:**
```
album_names_for_asset(): 942,569 calls!
Average cost: ~2.92s / 942,569 = 3.1 microseconds per call
```

**BUT** this suggests repeated queries for same albums:
- 26,562 assets
- 942,569 album lookups
- = ~35 lookups per asset on average

**Investigation Required:**
1. Add caching/memoization to `album_names_for_asset()`
2. Estimated hits: 80-90% (same albums queried repeatedly)
3. Potential savings: 750k+ operations → **1-2 seconds improvement** (minimal but easy)

**Implementation Effort:** Very Low (simple cache decorator)

**Files:**
- `immich_autotag/assets/asset_response_wrapper.py` - `album_names_for_asset()` method

---

### 🥉 **Priority 3: Connection Pooling Verification** (Network Layer)

**Current State:**
- 43,892 HTTP requests
- Likely not optimized for connection reuse

**Investigation Required:**
1. Check httpx configuration in immich_client:
   ```python
   client = Client(
       base_url=...,
       limits=Limits(max_connections=10),  # Is this set?
       ...
   )
   ```
2. Verify connection keep-alive headers
3. Check if DNS lookups are cached
4. Measure connection reuse ratio

**Potential Savings:** 5-10% if connection overhead is high

**Implementation Effort:** Low (config tuning)

**Files:**
- `immich-client/immich_client/client.py` or similar

---

### 🔷 **Priority 4: Async/Await Refactoring** (High Effort, High Reward)

**Current State:**
- Pure synchronous code with thread-unsafe shared state

**What This Would Enable:**
```python
# Instead of sequential 107 search calls:
tasks = [search_assets(page_i) for i in range(107)]
results = await asyncio.gather(*tasks)  # Concurrent!

# Result: ~10x speedup on search operations alone
```

**Potential Savings:** 10-20% overall (if properly implemented)

**Implementation Effort:** Very High (requires major refactoring)

**Timeline:** Post 2026-Q1

**Files Affected:**
- All API interaction code
- Asset management pipeline
- Context initialization

---

## Next Steps (Immediate Actions)

### **Week 1: Validate Lazy-Loading**
- [ ] Jenkins run completes (In Progress)
- [ ] Extract profile(1).stats from artifacts
- [ ] Compare get_asset_info calls vs baseline
- [ ] Confirm expected 5-15% improvement or investigate why not

### **Week 2: Investigate Batch Operations**
- [ ] Document Immich API batch capabilities
- [ ] Prototype batch tag operation
- [ ] Estimate savings

### **Week 3: Implement High-ROI Fix**
- [ ] Implement highest ROI optimization
- [ ] Profile new version
- [ ] Validate improvement

---

## Decision Tree: Which Optimization to Pursue?

```
Jenkins lazy-loading results:
├─ Improvement > 10%?
│  └─ YES → Good! Pause optimizations, merge to main, document
│  └─ NO → Continue below
│
├─ Improvement 5-10%?
│  └─ YES → Acceptable. Plan Priority 1 (batching) next quarter
│  └─ NO → Continue below
│
└─ Improvement < 5%?
   └─ Investigate Priority 1 immediately (batching must be done)
      └─ Can we batch tags? YES → Implement immediately
      └─ Can we batch tags? NO → Async/await is necessary
```

---

## Performance Prediction Model

Given `X` API calls with average latency `L`:

```
Total Time ≈ X × L + CPU_processing + Overhead

Current (seq): 43,892 calls × 36.73ms + 126s CPU ≈ 3,427s

Optimizations:
├─ Lazy-loading (10% reduction):   39,502 calls × 36.73ms ≈ 3,297s (-130s, -3.8%)
├─ + Batch tags (3,857 → 40 calls):    36,585 calls × 36.73ms ≈ 3,019s (-408s, -11.9%)
├─ + Batch search (0% if no gain):   Similar ≈ 3,019s
├─ + Album cache (942k ops):         ~2,970s (-49s, -1.4%) ≈ 2,970s (-14.3% total)
└─ + Async read (50% parallelism):   18,293 calls × (36.73/2)ms + overhead ≈ 2,000s (-41% total)
```

**Realistic targets:**
- **Conservative (Lazy + Batch):** 3,000-3,100s (12-15% improvement)
- **Moderate (Lazy + Batch + Cache):** 2,900-3,000s (15-18% improvement)
- **Aggressive (Async):** 2,000-2,200s (40-45% improvement, requires major work)

---

## Risk Assessment

| Optimization | Complexity | Risk | Effort | ROI |
|---|---|---|---|---|
| Lazy-loading | Low | Very Low | Low | ✓ (DONE) |
| Batch tags | Medium | Low | Medium | High (5-10%) |
| Album cache | Very Low | None | Low | Low (1-2%) |
| Async/await | Very High | High | Very High | Very High (40%+) |

---

## Success Metrics

For each optimization, measure:
1. **Total execution time** vs baseline
2. **API call count** by type (search, get_asset_info, tag, album, etc.)
3. **Socket I/O time** (subset of profile)
4. **Memory peak usage**
5. **Profile hotspots** (identify new bottleneck)

---

## Strategic Goals (2026 Q1-Q2)

| Goal | Target | Effort | Owner |
|------|--------|--------|-------|
| **Lazy-loading validation** | Confirm 5-15% | In Progress | AI/Team |
| **Batch operations prototype** | Proof-of-concept | 1 week | Team |
| **Album caching** | Quick win | 2 days | Team |
| **Performance dashboard** | Real-time metrics | 2 weeks | DevOps |
| **Async evaluation** | Technical design | 1 week | Tech Lead |

---

## Appendix: Commands for Profiling Comparison

### Extract Key Metrics from profile.stats

```bash
# Compare two profile runs
python -c "
import pstats
p1 = pstats.Stats('profile(1).stats')
p2 = pstats.Stats('profile(2).stats')

# Find get_asset_info calls
for func, (cc, nc, tt, ct, callers) in p1.stats.items():
    if 'get_asset_info' in func[2]:
        print(f'Run 1: {nc} calls')

for func, (cc, nc, tt, ct, callers) in p2.stats.items():
    if 'get_asset_info' in func[2]:
        print(f'Run 2: {nc} calls')
"

# Create flamegraph comparison
py-spy record -o profile1.svg --pid <pid1>
py-spy record -o profile2.svg --pid <pid2>
# Compare in browser
```

---

## Sign-Off

**Document prepared:** 2026-01-16  
**Status:** Ready for execution pending lazy-loading validation  
**Next review:** Upon Jenkins completion (expected 2026-01-16 evening)
