# 001-cleanup

## Maintenance task: one-time rescue operation

This document describes the first maintenance task to fix the problem of corrupted album names. This is not a regular product feature, but a one-time rescue operation to repair a specific issue: some albums have corrupted names due to repeated renaming actions. The goal is to restore the database integrity by undoing these unwanted renames and cleaning up duplicate album names.

### Context
The issue arose because albums were renamed multiple times, often unnecessarily, resulting in names like:

`2025-11-22-original_album_name__RENAMED_BY_AUTOTAG_DUPLICATE_USER_ALBUM__RENAMED_BY_AUTOTAG_DUPLICATE_USER_ALBUM`

This pattern is present in many albums, and we want to undo these actions and restore the original names where possible.

### Process
- This code will be included in the product, but only as a rescue tool.
- It will be executed once to fix the corrupted database.
- After execution, the code will remain available for future emergencies, but will be disabled by default (controlled by a development config flag).
- When this functionality is activated, the product will only perform this rescue operation; no asset processing or other product features will run.
- The purpose is to repair the database, not to provide ongoing duplicate handling.

### Implementation notes
- The process will identify albums with corrupted names and attempt to restore their original names.
- Duplicate albums will be merged or cleaned as needed.
- The operation is designed to be safe and idempotent, ensuring no further corruption.

### Configuration
- Activation is controlled by a flag in the internal config file.
- When enabled, only this rescue process runs.

---
This folder will contain all documentation and code related to this one-time cleanup step. Further steps will follow after the database is repaired.