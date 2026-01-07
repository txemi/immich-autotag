# Changelog

All versions follow [Semantic Versioning](https://semver.org/).

## [0.10] - 2025-12-23
### Added
# **Info:** The official release tag for version 0.10 is [`v0.10`](https://github.com/txemi/immich-autotag/releases/tag/v0.10) on the `main` branch.
- Clear definition of asset categories using configuration files.
- Automatic tags to inform users about categorized and uncategorized assets.
- Conflict tags when categorization issues are detected.

# [0.20] - 2026-01-07
### Added
- Automatic detection and **date repair** of asset dates based on file names and duplicate analysis.
- Auto-assignment of classification tags and albums based on duplicate assets.
- Option to remove leading/trailing spaces from album names for cleaner organization.
- New loop script for continuous asset tagging/classification during heavy editing sessions.
- Ability to exclude sets of assets from processing by specifying their web link (asset link exclusion).
- New log file for modification reports, tracking all changes made during processing.
- New statistics file with counters for the number of assets remaining to be classified and the number of conflicts detected.
- **Experimental:** Ability to resume processing from the last processed asset (checkpoint resume). *(Not enabled by default; will be improved in the next version.)*
- **Experimental:** Ability to create and assign albums based on folders from the file system library. *(Not enabled by default; will be improved in the next version.)*



## [0.30] - YYYY-MM-DD
### Added
- New, more structured configuration system for easier and safer customization.
- More abstract and flexible asset categorization, based on tags and albums, allowing for broader and more powerful organization than previous strict approaches.
- Consolidation of experimental features from version 0.20:
  - Resume processing from the last processed asset (checkpoint resume) is now stable and enabled by default.
  - Creation and assignment of albums based on folders from the file system library is now stable and enabled by default.


## [1.0] - YYYY-MM-DD
### Added
- Robust, uninterrupted processing of large photo sets (tested with 270,000 sample photos).
- Considered stable and complete for intensive use.
