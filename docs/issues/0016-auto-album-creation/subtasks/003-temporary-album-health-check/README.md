
# Subtask: Temporary Album Health Check and Automatic Deletion

**Date:** January 19, 2026  
**Status:** Design and initial documentation  
**Parent Issue:** 0016 - Auto Album Creation from Date  
**Proposed:** As subtask of 0016

---

## Context and Problem

When temporary albums are created to group unclassified assets, it may happen that, after fixing the file dates (e.g., with a "fix date" feature), a temporary album ends up containing assets with very distant dates. This breaks the purpose of the temporary album (grouping assets from a single day) and confuses the user.

## Subtask Objective

- Automatically detect when a temporary album is no longer useful because it contains assets with widely separated dates (configurable threshold, default 10 days).
- Automatically delete the temporary album before adding a new asset, so the normal flow will recreate it correctly and group assets from a single day again.

## Proposed Algorithm

1. Before adding an asset to a temporary album, check if the album is "healthy":
   - Iterate over the album's assets (optimize: early exit, do not process all if not needed).
   - Calculate the minimum and maximum date.
   - If the difference exceeds the threshold (default 10 days), mark the album as invalid.
2. If the album is not valid:
   - Delete it automatically.
   - The main flow will continue and recreate the album, adding the asset correctly.

## Justification for Insertion Point

- This check will be performed in the temporary album management logic, not in the generic method for adding assets to any album.
- This keeps responsibilities separated and avoids penalizing the performance of normal albums.

## Pending Implementation

- Temporary album health validation function.
- Integration in the temporary album creation/assignment flow.
- Threshold configuration.
- Logging and ModificationReport registration.

---

## Relation to Other Subtasks
- 001-create-temporary-albums: creation of temporary albums.
- 002-cleanup-from-temporary-albums: cleanup of assets from temporary albums when they already have classification.

---

## Notes
- This logic is idempotent and concurrency-safe.
- The user does not lose information: the album is automatically recreated if needed.
