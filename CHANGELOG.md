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


## Unreleased
**Description:** Adds automatic creation of daily albums for assets that do not belong to any album, using easily identifiable names for user review.
**Status:** Frozen — will be released soon.
### Added
- Automatic creation of albums named by day (e.g., `Review YYYY-MM-DD`) for assets that are not assigned to any album, making it easy for users to review and organize unclassified photos by date.


### Note — Performance regression under investigation
- **Observed behavior:** Recent runs of the representative test battery have shown a significant runtime regression: test executions that historically completed in ~4 hours have been observed to take 14–15 hours in the most recent runs. The exact numbers vary between runs and datasets; this regression is under active investigation.
- **Possible causes:** The root cause is not yet confirmed. Potential contributing factors include a sudden increase in the number of albums created during processing or changes in application code that increase work per asset. Profiling artifacts have been enabled and are being collected to help identify hotspots (see linked issue).
- **Status & action:** The issue is being tracked and analyzed in [issue 0021 — Profiling & Performance Reports](docs/issues/0021-profiling-performance/). CI profiling has been enabled on a dedicated performance branch and profiling artifacts (CPU profiles, pstats, flamegraphs) are being archived for analysis. Further updates and findings will be posted to the linked issue.
- **Impact & unknowns:** At this time we cannot predict which users or datasets are affected or the precise origin of the slowdown. Ongoing analysis will try to reproduce the regression, narrow down its cause, and propose fixes or mitigations.

### Configuration / Breaking changes
- **Checked for config format changes:** I reviewed repository configuration docs and recent changes; there is no indication of a configuration-format breaking change introduced specifically in this Unreleased entry relative to `v0.71.0`.
- **Historical note:** The major configuration-system change (Python + YAML structured config support) was introduced in v0.25 (see [issue 0009 — Config system refactor](docs/issues/0009-config-system-refactor/)). If you know of a specific config-file change or commit that should be considered breaking in this Unreleased version, please point me to it and I will add a formal "Breaking changes" entry.



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
