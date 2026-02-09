# Duplicate Name Album Recovery Plan

## 1. Context and Terminology Clarity

- The current issue is database contamination due to albums with duplicate names.
- In the product, "duplicate" can refer to photos or album names. Here, we focus on album names.
- From now on, methods and comments must clarify the context of "duplicate" to avoid confusion.

## 2. Procedure 1: Album Name Cleanup

- Create a maintenance function to undo all automatic album renames (duplicate suffix).
- This function is activated via a flag in the configuration (`Internet config`).
- When activated, the function:
  - Finds all albums whose name contains the duplicate pattern.
  - Removes the pattern and everything after it (may appear multiple times).
  - Executes with extreme care to avoid data loss.
  - After cleaning, terminates the process (no asset or photo processing).

## 3. Procedure 2: Duplicate Detection and Resolution

- In a normal run, before processing assets:
  - Execute robust logic to detect and resolve album name duplicates.
  - Fix duplicates before continuing with normal processing.

## 4. Procedure 3: Fail Fast During Processing

- While processing assets:
  - Do not attempt to fix duplicates on the fly.
  - If a duplicate is detected, throw an exception and stop the process.
  - This prevents mixing objectives and losing control.

## 5. Task Management and Documentation

- This document should be placed in the documentation folder, in the task manager organized by features.
- Create a subfolder for each step of the process.
- Document each subprocess and use task management to track progress.

---

### Next Steps

1. Place this document in the task/feature folder for duplicate name albums.
2. Create subfolders for:
   - Name cleanup (procedure 1)
   - Pre-processing duplicate resolution (procedure 2)
   - Fail-fast processing (procedure 3)
3. Implement the cleanup function and activate the flag.
4. Document and organize the next steps in task management.
