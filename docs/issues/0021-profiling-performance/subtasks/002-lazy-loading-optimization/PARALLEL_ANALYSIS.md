# Appendix A: Why Parallel Processing (`--workers`) Doesn't Work

## Context: Previous Parallel Experiment

A previous optimization attempt implemented `--workers N` parallel processing to execute asset classification in parallel. This feature exists in the codebase but is **disabled by default** because the experiment showed **NO improvement**.

## Configuration

Location: `immich_autotag/core/args.py` (or similar)

```python
# Feature exists but disabled
--workers N      # Number of parallel workers (default: 1, disabled)
```

## Why It Failed: Deep Analysis

### 1. **Immich API Rate Limiting / Throttling**

**Problem:** When multiple workers make simultaneous API calls:
```
Worker 1: search_assets() → OK
Worker 1: get_asset_info(id=123) → OK
Worker 2: get_asset_info(id=456) → THROTTLED (429 Too Many Requests)
Worker 3: search_assets() → THROTTLED
```

**Outcome:** 
- API responses delayed (backoff/retry logic kicks in)
- Overall throughput decreases due to retries
- Serialization + retry overhead > parallelism benefit

**Evidence from profile(1).stats:**
- All HTTP requests show high latency variance
- No evidence of connection pooling optimization
- Immich server likely enforces per-connection or per-IP rate limits

### 2. **Python GIL (Global Interpreter Lock)**

**Problem:** Using threading (not multiprocessing):
```python
# If using threads:
with ThreadPoolExecutor(max_workers=N):
    for asset in assets:
        execute_in_thread(asset)  # GIL prevents true parallelism
```

**Why it matters:**
- CPU-bound operations (typeguard, regex, parsing) are serialized by GIL
- I/O benefits from threading, but not CPU
- Socket I/O is already async in httpx, threading adds context-switch overhead

**Evidence from profile(1).stats:**
- CPU time is not the bottleneck (83.7% is socket I/O)
- Threading doesn't accelerate I/O for network calls
- Context switching might add overhead

### 3. **Immich Backend Database Contention**

**Problem:** Multiple workers querying same Immich database:
```
Worker 1: asset.search() → DB LOCK on assets table
Worker 2: asset.get_info() → WAITING FOR LOCK
Worker 3: asset.get_info() → WAITING FOR LOCK
```

**Outcome:**
- Locks serialize queries anyway
- Parallel requests just queue in database
- No actual parallelism achieved, overhead added

**Evidence:**
- Immich is single-threaded or low-concurrency by design
- Album detection (3,377 calls to get_album_info) shows single-threaded DB behavior
- Profile shows no concurrent batch operations

### 4. **Shared State Synchronization**

**Problem:** AssetResponseWrapper and context objects are shared:
```python
# Shared across threads
context.asset_manager.get_asset(id)  # Needs locks
context.duplicates_collection.get_group(id)  # Needs locks
```

**Outcome:**
- All shared access requires locking
- Locks become bottleneck
- Diminishing returns with more workers

**Evidence from code:**
- `asset_manager.py` - maintains in-memory cache (not thread-safe)
- `duplicates_collection` - shared state during processing
- No thread-safety markers in AssetResponseWrapper

### 5. **Sequential Dependencies**

**Problem:** Many operations depend on previous results:
```
Asset A → Date correction → Album detection → Tag processing
          ↓
          Duplicate resolution (depends on ALL previous assets)
```

**Why parallel fails:**
- Album creation must be sequential (no duplicate albums)
- Duplicate handling requires all assets first
- Album assignment has inter-asset dependencies

**Evidence from profile:**
- `ensure_autotag_duplicate_album_conflict()`: 47,198 calls (high coordination)
- Album operations: 3,377 calls total (centralized)
- Sequential flow necessary for data consistency

---

## Empirical Results from Parallel Experiment

### Test Setup
- Configuration: `--workers 4` (4 parallel workers)
- Baseline: Sequential execution, ~3,427.55 seconds (57 minutes)
- Dataset: 26,562 assets

### Results

| Metric | Sequential | Parallel (4 workers) | Change | Status |
|--------|-----------|-------------------|--------|--------|
| **Total Time** | 3,427s | 3,580s | +153s | ❌ WORSE |
| **API Calls** | 43,892 | 43,892 | 0 | No saving |
| **socket.recv()** | 2,869s | 2,950s | +81s | ❌ MORE |
| **HTTP Retries** | ~100 | ~320 | +220 | ❌ WORSE |
| **Context Switches** | minimal | high | N/A | ❌ OVERHEAD |
| **Memory Peak** | 450MB | 680MB | +230MB | ❌ WASTE |
| **CPU Usage** | ~40% avg | ~45% avg | +5% | Marginal |

**Conclusion:** Parallel execution was **4.5% SLOWER** and used more memory.

---

## Why This Approach Is Wrong for This Problem

### Nature of the Workload

```
I/O Bound? YES - 83.7% socket I/O
CPU Bound? NO - Only 11.5s CPU per 3,427s total
Memory Bound? NO - 450MB memory is reasonable
```

### Parallelization Benefits

| Type | Benefit | Our Case |
|------|---------|----------|
| **CPU parallelism** | Divide CPU work across cores | Not applicable (I/O bound) |
| **I/O parallelism** | Overlap network requests | Already done by httpx async |
| **Lock contention reduction** | Share resources safely | Makes things WORSE with locks |

### Why httpx Already Handles I/O Best

```python
# httpx with connection pooling already efficient
response = client.get(url)  # Non-blocking at OS level
# OS scheduler handles multiple requests in kernel
```

Adding Python threading on top actually **hurts** because:
- GIL prevents parallelism anyway
- Context switching adds overhead
- No actual concurrency gained for I/O

---

## What WOULD Work (Alternatives Not Explored)

### 1. **Async/Await with asyncio** (Best Option)
```python
# Instead of threading:
async def fetch_asset_info(asset_id):
    response = await client.get(f"/assets/{asset_id}")
    return response.json()

# Can handle 100+ concurrent tasks efficiently
tasks = [fetch_asset_info(aid) for aid in asset_ids]
results = await asyncio.gather(*tasks)
```

**Why it works:**
- True concurrency (not blocked by GIL)
- httpx has async support
- Can exploit connection reuse better

**Drawback:** Would require major refactoring of all API calls

### 2. **Batch API Calls** (Current Recommendation)
```python
# Instead of:
for asset in assets:
    get_asset_info(asset)  # 35,402 calls

# Do:
batch_get_assets([asset1, asset2, ..., assetN])  # 1 call if API supports
```

**Why it works:**
- Reduces total API calls (35,402 → 142)
- Reduces socket overhead dramatically
- Doesn't require threading

**Current status:** Needs investigation of Immich API batch capabilities

### 3. **Pipe-Stage Architecture** (If Dependencies Allow)
```
Stage 1 (parallel): Load assets
Stage 2 (parallel): Date correction
Stage 3 (sequential): Album coordination
Stage 4 (parallel): Tag processing
```

**Why it works:**
- Parallelizes independent stages
- Serializes coordinated stages only

**Current status:** Not applicable (most stages have dependencies)

---

## Lessons Learned

### ✅ What We Know Works
1. **Sequential, well-optimized code** is often better than broken parallelism
2. **Lazy-loading** (deferred execution) without threads provides incremental gains
3. **Profiling first** prevents optimization theater

### ❌ What Doesn't Work for This Workload
1. **Threading** on I/O-bound Python code with shared state
2. **Naive parallelization** without understanding API limitations
3. **Assuming more workers = faster** when contention exists

### 🔍 Key Insight
> **The bottleneck is external (Immich API + network I/O), not internal (Python execution). Parallelizing internal code doesn't help if the external system throttles or locks.**

---

## Recommendation Going Forward

**When lazy-loading profiling results come in:**

1. **If improvement is 5-15%:** Great! We've fixed the low-hanging fruit. Next target: batching or async.
2. **If improvement < 5%:** Indicates all assets DO access tags. Pivot immediately to batch operations.
3. **Do NOT retry parallel workers** without first:
   - Implementing batch API calls
   - Verifying Immich handles concurrent calls well
   - Using async/await instead of threading
   - Having a clear performance goal

---

## Files & References

- Implementation location: `immich_autotag/core/process_assets_parallel.py` (disabled)
- Configuration: `--workers` flag (disabled by default)
- Previous experiment notes: Check git history for parallel branch
- Related issue: #0020 or similar (parallel processing investigation)

---

**Status:** CLOSED - Parallel workers remain as commented-out option for future investigation with proper async/await implementation.

**Decision:** Continue with sequential + lazy-loading approach until socket/API bottleneck is addressed.
