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
- Documentación mejorada en CONTRIBUTING.md y README.md, incluyendo invitación explícita a contribuir en la reactivación de CI/CD (GitHub Actions). Consulta o participa en la discusión en GitHub: https://github.com/txemi/immich-autotag/issues/32
- Preparando nueva versión para publicar estos cambios y facilitar la colaboración de la comunidad.

## [Unreleased]
**Description:** Improvements to the rule engine: more abstract, supports not only regex but also simplified common use cases.
### Added

- The internal categorization flow has been adapted to fully leverage the new configuration system introduced in v0.25, enabling more versatile categorizations based on multiple tags and flexible album patterns. ([issue](docs/issues/0009-config-system-refactor/))
- Consolidation of experimental features from version 0.20:
  - Resume processing from the last processed asset (checkpoint resume) is now stable and enabled by default. ([issue](docs/issues/0008-statistics-checkpoint/))
  - Creation and assignment of albums based on folders from the file system library is now stable and enabled by default. ([issue](docs/issues/0004-album-detection/))



## [1.0] - YYYY-MM-DD
### Added
- Robust, uninterrupted processing of large photo sets (tested with 270,000 sample photos). ([issue](docs/issues/0008-statistics-checkpoint/))
- Considered stable and complete for intensive use.
