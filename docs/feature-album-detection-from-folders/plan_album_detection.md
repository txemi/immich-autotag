# Improvement Plan for Album Detection and Management

## User Requests

1. **Prevent file name from being used as album name**
   - Currently, if the folder logic fails or does not find a valid folder, it may end up using the file name as the album name.
   - Must ensure that only folder names are used, never the file name.

2. **Albums created but not visible/accessible**
   - Albums are created via API, but do not appear in the interface or you do not have access.
   - Diagnosis: Do they really exist? Are they assigned to any user? Is there a delay or bug in Immich?
   - Solution: Verify existence via API, check assigned users, assign user if necessary, and log the creation/assignment.

3. **Adapt the logging system to record actions on albums**
   - The current log only records actions on tags.
   - Should be generalized to support different entities (tag, album, etc.) and actions (add, remove, create, rename, ...).
   - Proposed log structure:

| datetime           | entity_type | action   | asset_id | asset_name | album_id | album_name | tag_name | user | details | link |
|--------------------|-------------|----------|----------|------------|----------|------------|----------|------|---------|------|
| 2025-12-23T12:34   | album       | create   | ...      | ...        | ...      | ...        |          | ...  | ...     | ...  |
| 2025-12-23T12:35   | album       | rename   | ...      | ...        | ...      | ...        |          | ...  | old_name=..., new_name=... | ... |
| 2025-12-23T12:36   | tag         | add      | ...      | ...        |          |            | autotag  | ...  |         | ...  |

- **entity_type:** 'tag', 'album', etc.
- **action:** 'add', 'remove', 'create', 'rename', etc.
- **asset_id/asset_name:** if applicable.
- **album_id/album_name:** if applicable.
- **tag_name:** if applicable.
- **user:** if applicable.
- **details:** free field for additional information (e.g., old_name/new_name in rename).
- **link:** relevant link (photo, album, etc.).

## Suggested Action Plan

1. Refactor the album detection logic to exclude the file name.
2. Diagnose and correct the visibility/assignment of created albums.
3. Redesign and adapt the logging system to support actions on albums and tags.
4. (Optional) Add tests and usage examples.

---

This document will serve as a reference for the development and debugging of album detection and management functionality, as well as for traceability of actions in the system.
