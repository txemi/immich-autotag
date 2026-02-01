# Issue 0016 - Auto Album Creation: Navigation & Progress

**Main Issue:** Auto Album Creation from Date When No Classification Album Found  
**Status:** In Progress  
**Created:** 2026-01-14  
**Updated:** 2026-01-17

---

## Overview

Issue 0016 implements a complete system for automatically creating temporary albums for unclassified assets, with mechanisms for cleanup and management.

This issue is organized into **subtasks**, each representing a distinct phase of work with its own timeline, branch, and deliverables.

---

## Subtasks Roadmap

### ✅ Subtask 001: Create Temporary Albums from Date (COMPLETED)

**Status:** Completed  
**Timeline:** Initial implementation phase  
**Deliverables:**
- Automatic album creation for unclassified assets
- Pattern: `YYYY-MM-DD-autotag-temp-unclassified`
- Config flag: `create_album_from_date_if_missing`

**Documentation:**
- `subtasks/001-create-temporary-albums/README.md` - Completion summary
- `subtasks/001-create-temporary-albums/ARCHITECTURE.md` - Original design (reference)
- `subtasks/001-create-temporary-albums/REQUIREMENTS.md` - Original requirements (reference)

**Implementation File:**
- `immich_autotag/assets/albums/create_album_if_missing_classification.py`

**Status Notes:**
These design documents represent **initial analysis** of this phase. Implementation is complete and integrated into feat/album-permission-groups.

---

### 🔄 Subtask 002: Cleanup - Remove Assets from Temporary Albums (IN PROGRESS)

**Status:** Analysis phase (not yet started)  
**Timeline:** Post-stabilization (after current test battery)  
**Estimated Duration:** 7-10 hours  
**Target:** Separate feature branch (feat/0016-cleanup or similar)

**Purpose:**
- Remove assets from temporary albums when they gain legitimate classification
- Solve race condition artifacts (asset in both temp + classification album)
- Keep temporary albums clean and meaningful

**Documentation:**
- `subtasks/002-cleanup-from-temporary-albums/IMPLEMENTATION_PLAN.md` - Full analysis & design

**Implementation Plan:**
1. Add `remove_asset()` method to `AlbumResponseWrapper`
2. Create `remove_from_autotag_albums.py` helper
3. Integrate cleanup into `analyze_and_assign_album.py`
4. Add config flag: `remove_asset_from_autotag_temporary_albums`
5. Unit + integration testing

**Status Notes:**
Blocked on: Current Jenkins builds stabilizing (approx 87 hours remaining)  
Not blocking: Release v0.72-v0.73 (optional enhancement)

---

## Quick Navigation

### For Implementation Work
- **Current work:** See Subtask 002 IMPLEMENTATION_PLAN.md for full design
- **Ready to code:** All analysis complete, waiting for stabilization window

### For Design Reference
- **Original requirements:** `subtasks/001-create-temporary-albums/REQUIREMENTS.md`
- **Original architecture:** `subtasks/001-create-temporary-albums/ARCHITECTURE.md`

### For Parent Issue Context
- **Main README:** `readme.md` (parent issue overview)

---

## Branch Strategy

| Subtask | Branch | Status |
|---------|--------|--------|
| 001 | Multiple (merged) | ✅ Complete |
| 002 | `feat/0016-cleanup` (planned) | 🔄 Not started |

---

## Key Design Decisions

### Why Subtasks?
- Each phase has distinct timeline and deliverables
- Allows parallel analysis while prioritizing stabilization
- Clear separation between "initial design" (001) and "evolution" (002)
- Easier to track progress and dependencies

### Race Condition Solution
- **Problem:** Assets in both temporary + classification album
- **Solution:** Cleanup phase (002) removes from temporary when classified
- **Safety:** Idempotent operation, doesn't delete albums, only membership

### Configuration-Driven
- Feature flags allow disabling if needed
- Users can disable cleanup for safety concerns
- Default: cleanup enabled (temporary albums should be temporary)

---

## Timeline Estimate

| Phase | Start | Duration | Status |
|-------|-------|----------|--------|
| 001 Create | Past | ~10h | ✅ Done |
| Stabilize | Now | ~87h | ⏳ In Progress (Jenkins builds) |
| 002 Cleanup | After stable | ~7-10h | 🔄 Queued |

---

## Related Issues

- **#0009:** Config system (established flags used here)
- **#0004:** Album detection (base logic reused)
- **#0021:** Profiling (performance tests will validate this)

---

## Notes

- Design documents in subtask folders represent **historical snapshots** of each phase
- Current status takes precedence over design docs
- Both subtasks follow same pattern as Issue 0021 (profiling)
- Subtask numbering allows for future intermediate tasks (e.g., 001.5 if needed)

