# Changelog

All versions follow [Semantic Versioning](https://semver.org/).


## [0.10] - 2025-12-23
**Description:** First version with automatic tags based on criteria, laying the groundwork for a future rule engine and conflict detection.
### Added
# **Info:** The official release tag for version 0.10 is [`v0.10`](https://github.com/txemi/immich-autotag/releases/tag/v0.10) on the `main` branch.
- Clear definition of asset categories using configuration files. ([issue](docs/issues/0010-core-tagging-feature/))
- Automatic tags to inform users about categorized and uncategorized assets. ([issue](docs/issues/0010-core-tagging-feature/))
- Conflict tags when categorization issues are detected. ([issue](docs/issues/0010-core-tagging-feature/))

# [0.20] - 2026-01-07
**Description:** Adds date repair, asset exclusions, improved statistics, checkpoint resume, and automatic album creation.
### Added
- Automatic detection and **date repair** of asset dates based on file names and duplicate analysis. ([issue](docs/issues/0008-statistics-checkpoint/))
- **Automatic classification of photos based on duplicates:** auto-assignment of classification tags and albums when duplicate assets are detected. ([issue](docs/issues/0003-duplicates-management/))
- Option to remove leading/trailing spaces from album names for cleaner organization. ([issue](docs/issues/0004-album-detection/))
- New loop script for continuous asset tagging/classification during heavy editing sessions. ([issue](docs/issues/0004-album-detection/))
- Ability to **exclude sets of assets** from processing by specifying their web link (asset link exclusion). ([issue](docs/issues/0005-filter-assets/))
- **New log** file for modification reports, tracking all changes made during processing. ([issue](docs/issues/0008-statistics-checkpoint/))
- **New statistics** file with counters for the number of assets remaining to be classified and the number of conflicts detected. ([issue](docs/issues/0008-statistics-checkpoint/))
- **Experimental:** Ability to resume processing from the last processed asset (checkpoint resume). *(Not enabled by default; will be improved in the next version.)* ([issue](docs/issues/0008-statistics-checkpoint/))
- **Experimental:** Ability to **automatically create and assign albums** based on folders from the file system library. *(Not enabled by default; will be improved in the next version.)* ([issue](docs/issues/0004-album-detection/))

# [0.25] - 2026-01-09
**Description:** Major configuration system upgrade as preparation for a more abstract and flexible rule engine.
### Added
- New, more structured and flexible configuration system, allowing configuration to be defined both in Python code and in a YAML text file. ([issue](docs/issues/0009-config-system-refactor/))
- Enables advanced customization and configuration validation, improving security and user experience. ([issue](docs/issues/0009-config-system-refactor/))
- New, more structured configuration system for easier and safer customization. ([issue](docs/issues/0009-config-system-refactor/))
- More abstract and flexible asset categorization, based on tags and albums, allowing for broader and more powerful organization than previous strict approaches. ([issue](docs/issues/0009-config-system-refactor/))

# [0.30] - 2026-01-09
**Description:** First public release as a Python package (PyPI) with instant CLI support and easy installation for all users.
### Added
- **Instant CLI execution from PyPI:** Users can now run the autotagging application with a single command, thanks to full pipx support and streamlined packaging. No manual setup or environment creation required—just copy your configuration and launch!
- **Quick Start documentation:** Clear instructions and links for configuration, enabling new users to get started in seconds.
- **Self-documented configuration templates:** Both YAML and Python configuration templates are now provided and fully documented, making setup and customization effortless.

> This release marks a major milestone in usability: Immich autotag can be installed and executed directly from the repository or PyPI, making it accessible to everyone with minimal effort.


## [0.40] - 2026-01-10
**Description:** First release with container support (Docker). Initial, provisional containerization system for scheduled and automated runs.
### Added
- Support for running as a containerized service, enabling scheduled executions to keep tagging and corrections up to date automatically, without requiring manual script launches after manual updates or categorizations. ([issue](docs/issues/0011-container-scheduled-execution/))

## [0.45.7] - 2026-01-11
**Description:** Major improvement of the statistics and logging system for better traceability and robustness.
### Changed
- Logging and statistics system refactored for robustness and traceability.
- Now both the runtime git describe (from the current repo, if available) and the distributed package git describe (from version.py) are recorded in statistics, making it easier to trace the exact code version used in any environment (including Docker or PyPI installs).
- The statistics file is now written immediately at application startup, ensuring it is always available for monitoring and debugging from the very beginning of each run.
- All code, comments, and log messages are now in English for consistency and maintainability.

## [0.70.7-2-g8b496cb-dirty] - 2026-01-12
**Description:** Work in progress: automating Python package and container generation using GitHub Actions and various improvements. Not final.
### Changed
- Ongoing automation for Python package and container builds (GitHub Actions integration, improvements in packaging and CI/CD workflows).
- Improved documentation in CONTRIBUTING.md and README.md, including an explicit invitation to contribute to the reactivation of CI/CD (GitHub Actions). See or join the discussion on GitHub: https://github.com/txemi/immich-autotag/issues/32
- Preparing a new release to publish these changes and facilitate community collaboration.

## [0.71.0] - 2026-01-14
**Description:** GitHub Actions workflow enablement for automated PyPI and Docker Hub publishing.
### Added
- **Automated PyPI publishing via GitHub Actions:** The release workflow now automatically publishes the package to PyPI when a version tag is created.
- **Automated Docker Hub publishing:** Docker images (main and cron variants) are now automatically built and pushed to Docker Hub on release.
- **Immich client version fallback:** The setup script now uses a hardcoded fallback version (v2.4.1) when no Immich server configuration is available, enabling CI/CD environments to work without access to a real Immich server. ([issue](docs/issues/0015-github-actions-pypi-publishing/))

### Changed
- Improved release script workflow to ensure proper version tagging and consistency checking.

### Fixed
- GitHub Actions workflow now works correctly without requiring access to a private Immich server or API credentials. ([GitHub Issue #32](https://github.com/txemi/immich-autotag/issues/32))


## [0.72.0-rc1] - 2026-01-17
**Description:** Album permission groups - Phase 1 (detection and logging)
**Status:** Release candidate - ready for testing
**Commit:** `d8a3b1a`
**Branch:** `feature/user-group-policies`
**Release type:** Tag + version (no PyPI/Docker publishing)

### Added
- **Album Permission Groups - Phase 1:** Detection system for albums matching configured keywords
  - Detects which albums match configured user group keywords
  - Phase 1 performs detection and logging only (no API calls)
  - Foundation for Phase 2 synchronization
  - Link: [issue 0018 — Album Permission Groups](docs/issues/0018-album-permission-groups/)

### Features included
- Configuration-based user groups with member lists
- Keyword matching for album names
- Detection reporting and logging
- Dry-run mode for Phase 1

### Known issues
- None specific to Phase 1


## [0.72.0-rc2] - 2026-01-17
**Description:** Album permission groups - Phase 2 (synchronization - FULLY FUNCTIONAL)
**Status:** Release candidate - production ready, tested with 500+ albums
**Commit:** `c588cf7`
**Branch:** `feature/user-group-policies`
**Release type:** Tag + version (no PyPI/Docker publishing)

### Added
- **Album Permission Groups - Phase 2:** Complete synchronization system for album member management
  - Automatically adds configured members to matching albums
  - Automatically removes members no longer in configuration
  - Email→UUID resolution for member lookup
  - Idempotent operations (safe to run multiple times)
  - Link: [issue 0018 — Album Permission Groups](docs/issues/0018-album-permission-groups/)

### Changed
- Album permissions now execute BEFORE asset tagging for proper sequencing
- Configuration is source of truth - only configured members have access

### Fixed
- Email address resolution for album member management
- Proper handling of member additions and removals

### Testing
- ✅ Tested with 500+ albums, 3 members per group
- ✅ Verified idempotent behavior
- ✅ All permission changes applied correctly

### Known issues
- None specific to Phase 2


## [0.73.0-rc1] - 2026-01-17
**Description:** Type system centralization and authentication fixes
**Status:** Release candidate
**Commit:** `9c8e660`
**Branch:** `feat/album-permission-groups`
**Release type:** Tag + version (no PyPI/Docker publishing)

### Added
- **Client Type Centralization:** Unified `ImmichClient` type definition
  - New `immich_autotag/types.py` with canonical type alias
  - Eliminates scattered imports across codebase
  - Single source of truth for client configuration

### Fixed
- **AuthenticatedClient Configuration:** Immich-specific headers now correct
  - Changed from default "Bearer" token to "x-api-key" header format
  - Fixes 401 Unauthorized errors
  - Immich API now properly authenticated
- **Email→UUID Resolution:** New mapping system for album member emails
  - Converts configured member emails to Immich system user IDs
  - Prevents "badly formed hexadecimal UUID" errors
  - Essential foundation for Phase 2 synchronization

### Changed
- All code now uses centralized `ImmichClient` type
- ConfigManager initialization improved with better error handling

### Technical debt reduced
- Removed type inconsistencies across codebase
- Proper Immich API parameter handling


## [0.73.0-rc2] - 2026-01-17
**Description:** Lazy-loading optimization and performance improvements
**Status:** Release candidate
**Commit:** `ce834f8`
**Branch:** `perf/symmetric-rules-with-performance`
**Release type:** Tag + version (no PyPI/Docker publishing)

### Added
- **Lazy-Loading Optimization:** Asset tag data loaded on-demand
  - Significant memory and API call reduction
  - Faster initial asset retrieval
  - Conditional type checking for production performance (~50% speedup possible)

### Changed
- Asset tag loading now lazy (not eagerly fetched)
- Checkpoint save frequency optimized (every 100 assets vs every asset)
- Asset update operations batched to reduce API calls

### Performance improvements
- Reduced API call count during asset processing
- Lower memory footprint for large asset sets
- Faster test execution time

### Known issues
- **Performance regression under investigation:** Some production runs show 4h→14-15h slowdown
  - Possible causes: increased album creation count, per-asset code changes
  - Under analysis in [issue 0021 — Profiling & Performance Reports](docs/issues/0021-profiling-performance/)
  - CI profiling enabled on dedicated branch


## [0.73.0-rc3] - 2026-01-17
**Description:** Automatic album creation from unclassified assets
**Status:** Release candidate
**Commit:** `01370f3`
**Branch:** `feature/auto-album-creation-from-date`
**Release type:** Tag + version (no PyPI/Docker publishing)

### Added
- **Auto-Album Creation:** New feature for organizing unclassified assets
  - Automatically creates albums named by date (e.g., `Review YYYY-MM-DD`)
  - Creates albums for assets not assigned to any classification
  - Makes it easy for users to review and organize unclassified photos
  - Configurable via `create_album_from_date_if_missing` setting

### Changed
- Album decision logic refactored for better clarity
- Temporary albums created for assets without classification matches

### Features
- ImmichContext now uses singleton pattern for consistent state
- Album creation workflow integrated into main processing pipeline


## [0.73.0-rc4] - 2026-01-17
**Description:** Classification engine improvements - OR logic for rules
**Status:** Release candidate
**Commit:** `1451649`
**Branch:** `feature/rules-tag-album-combination`
**Release type:** Tag + version (no PyPI/Docker publishing)

### Added
- **Classification Rule Engine Enhancements:** OR logic for flexible rule matching
  - ClassificationRule now supports OR logic for combined criteria
  - Multiple tags or albums can match with OR semantics
  - Improved conflict handling for duplicate assets
  - Better logging of classification decisions

### Changed
- ClassificationRuleWrapper validation now uses OR logic
- Conflict handling improved with classification conflict tags
- Modification reports now include all classification decisions

### Fixed
- Duplicate asset conflict resolution improved
- Classification conflicts now logged with better context

### Features
- Links generated include input tags from classification rules
- Auto-album creation from asset date when no classification found


## [0.73.0] - 2026-01-17
**Description:** Complete release - Album permissions, type system, performance, auto-album creation (v0.72 + v0.73 consolidated)
**Status:** Release candidate → Release
**Commit:** `3fa53c6`
**Branch:** `feat/album-permission-groups` (current HEAD)
**Release type:** Tag + version (no PyPI/Docker publishing yet)

### Summary
This release consolidates significant work across 5 major feature areas:
1. ✅ Album permission groups (Phase 1+2, fully functional with 500+ album testing)
2. ✅ Type system centralization (Immich API fixes)
3. ✅ Performance optimizations (lazy-loading, checkpoint optimization)
4. ✅ Auto-album creation (for unclassified assets)
5. ✅ Classification engine improvements (OR logic, better conflict handling)

### Added
- **Configuration Internationalization:** Template now fully in English
  - User group names and examples translated
  - Configuration now suitable for international users
  - Link: docs/issues/0018-album-permission-groups/

- **Release Scripts Clarity:** Script documentation improved
  - `release.sh`: Version + tagging only (no publishing)
  - `full_release.sh`: Complete pipeline (version + PyPI + Docker)
  - Clear distinction prevents accidental public releases

- **Git Hygiene:** Profiling artifacts removed from repository
  - Removed `profile(1).stats` and `profile_optimized.stats`
  - Updated `.gitignore` to prevent future commits

### Changed
- All code comments and configuration now in English
- Script headers document PURPOSE and USE WHEN
- Release process clearly separated into two distinct modes

### Breaking changes
- None (config format compatible with v0.71.0)

### Known issues
- **Performance regression under investigation:** 4h→14-15h slowdown on profiling tests
  - Root cause not yet confirmed
  - Possible contributing factors: increased album creation, code changes per-asset
  - Being tracked and analyzed in [issue 0021](docs/issues/0021-profiling-performance/)
  - CI profiling enabled on dedicated branch
  - Impact: unknown which users/datasets affected, reproduction in progress

### Testing
- ✅ Album permissions Phase 1+2 tested with 500+ albums
- ✅ Type system validated with corrected Immich API calls
- ✅ Auto-album creation verified
- ✅ All Python code formatted and sorted
- ⚠️ Performance regression requires further investigation

### Next steps
- Resolution of performance regression (v0.74.0 focus)
- Further optimization of lazy-loading
- Potential PyPI/Docker publishing after performance stabilization



## [Planned: Compilation Albums Support]
**Description:** Adds support for "compilation" albums that can mix existing and newly added photos (for example, third-party or curated compilations). Classification behavior is relaxed for compilations so assets may belong to multiple albums or match multiple rules, while still providing validation warnings when an asset matches no rule.
### Added
- Support for "compilation" albums that combine existing and new photos, enabling curated or third-party collections.
- Relaxed classification rules for compilation albums: assets may belong to multiple albums or match multiple rule sets to reflect overlapping selections.
- A validation warning is generated when an asset in a compilation does not match any classification rule, helping users identify unclassified items.
### Changed
- Classification engine now supports multi-assignment semantics for assets within compilation albums; scoring and precedence logic adjusted to prefer stronger matches while allowing overlaps.

## [Planned: Profiling & CI Performance Reports]
**Description:** Add CI-integrated profiling and performance reporting so builds produce profiling artifacts and regressions can be detected automatically. See [issue 0021 — Profiling & Performance Reports](docs/issues/0021-profiling-performance/) for the issue details and implementation notes.
### Added
- CI jobs to run representative profiling workloads and archive CPU/memory profiles and flamegraphs.
- Threshold-based regression detection that flags significant slowdowns in representative workloads.
### Changed
- CI pipelines updated to include a small profiling step for representative workloads (configuration and thresholds to be defined in the issue linked above).

## [Planned: Code Quality Improvements (Sonar-like)]
**Description:** Introduce automated static analysis and code-quality gates using SonarQube or similar tools, and apply initial remediation to address the most critical findings.
### Added
- CI job configuration to run static analysis (SonarQube / SonarCloud or equivalent) on pull requests and main branches.
- A baseline report capturing current code quality metrics (bugs, vulnerabilities, code smells, coverage trends) to track improvement over time.
- Documentation for developers on how to run local scans and interpret Sonar reports (basic onboarding instructions).
### Changed
- CI pipeline modified to fail or warn builds based on configurable quality gates (e.g., new blocker issues, decreasing coverage, or rapidly rising hotspot counts).
- Project structure and packaging adjusted where necessary to enable more accurate analysis (e.g., excluding generated files, adding source roots for analyzers).
### Fixed / Remediated (initial)
- Addressed a prioritized subset of Sonar-style findings: high-priority security warnings and stability-related code smells reduced through targeted fixes and tests.


## [Planned: Date Correction Improvements]
**Description:** Planned improvements to date correction logic for edge cases and scenarios not currently handled correctly.
### Added
- Enhanced date extraction and correction for problematic or previously unhandled cases.

## [Planned: Album Creation Review]
**Description:** Planned review and overhaul of the automatic album creation system for better accuracy and flexibility.
### Added
- Refactored logic for automatic album creation, improving detection and assignment.

## [Unreleased]
**Description:** Improvements to the rule engine: more abstract, supports not only regex but also simplified common use cases.
### Added

- The internal categorization flow has been adapted to fully leverage the new configuration system introduced in v0.25, enabling more versatile categorizations based on multiple tags and flexible album patterns. ([issue](docs/issues/0009-config-system-refactor/))
- Consolidation of experimental features from version 0.20:
  - Resume processing from the last processed asset (checkpoint resume) is now stable and enabled by default. ([issue](docs/issues/0008-statistics-checkpoint/))
  - Creation and assignment of albums based on folders from the file system library is now stable and enabled by default. ([issue](docs/issues/0004-album-detection/))



## [Planned]
**Description:** Automatic creation of user permissions and user groups based on the rule engine.
### Added
- Automatic assignment of permissions to users according to rules.
- Creation and management of user groups for advanced access control.

## [1.0] - YYYY-MM-DD
### Added
- Robust, uninterrupted processing of large photo sets (tested with 270,000 sample photos). ([issue](docs/issues/0008-statistics-checkpoint/))
- Considered stable and complete for intensive use.
