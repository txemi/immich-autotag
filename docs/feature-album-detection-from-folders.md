# Feature: Album Detection from Folder Structure

## Intent and Objective

When an asset is not classified (i.e., does not belong to any album and does not have a category tag such as "meme"), attempt to infer a reasonable album name from the asset's folder path before proceeding with tag-based classification. This feature should be optional and controlled by a configuration flag (default: disabled), as some users may not want the software to create albums.

## Logic Overview

1. **Configuration Flag**
   - Add a boolean flag in the configuration file to enable/disable this feature. Default: `False`.

2. **Trigger Point**
   - Before performing tag logic for each asset (in the asset wrapper class), check if this feature is enabled.
   - If enabled, and the asset is not in any album and does not have a category tag, attempt album detection.

3. **Folder Path Analysis**
   - Collect all ancestor folders (and possibly the filename) for the asset.
   - For each folder (or filename), check if its name starts with a date in the expected format (ISO: `YYYY-MM-DD`).
   - Count how many folders match this date pattern.

4. **Decision Logic**
   - If no folders match, do nothing (proceed as usual).
   - If exactly one folder matches:
     - Use the folder name as the candidate album name.
     - Before creating/using the album, check if the folder name is suspiciously short (e.g., too few characters). If so, raise a `NotImplementedError` for further review.
   - If more than one folder matches:
     - Raise a `NotImplementedError` to force a review of this ambiguous case.

5. **Development Notes**
   - Use exceptions (not logs) for unhandled or ambiguous cases, as this feature is in development and should fail fast for unexpected scenarios.

---

## Documentation Practice

- Place this file in the `docs/` directory as `feature-album-detection-from-folders.md`.
- Each feature can have its own Markdown file in this directory.
- No need to use issue numbers if you are not tracking these in GitHub issues.

---

*This document describes the functional intent and logic for the album detection from folder structure feature. Update as the implementation evolves.*
