# 1. Roadmap: Immich AutoTag

> **Note:** This roadmap is pending update. For the most up-to-date information, please refer to the [Changelog](./CHANGELOG.md).


This document lists upcoming rules, features, and improvements planned for the Immich AutoTag project. Please update this file as new ideas or requirements arise.

Note: This roadmap lists upcoming features in order of priority, based on a subjective assessment of what delivers the most value and quick wins for the project.


## 1.1. Upcoming Features (to be prioritized)

1. **Album detection and creation from folders (IN PROGRESS):**
	If an album does not exist, implement logic to infer or create it based on folder structure.

	<!-- Planned for version 0.20 -->
    
	[See detailed design document →](docs/feature-album-detection-from-folders.md)
    
	**Current sub-tasks and context:**
	- We have started a major refactor to split the monolithic script into smaller, maintainable modules. This is necessary due to the growing complexity and size of the codebase.
	- Temporarily, configuration is being handled as Python code inside the package to allow for code fragments and easier refactor. There is an open issue to migrate to a more standard config system after refactoring.
	- The logging/reporting system is being updated: the tag modification report will soon also track other types of modifications (not just tag changes), to support broader asset operations and debugging.
	- The folder-based album detection logic is currently paused while we complete the refactor and logging improvements, to ensure maintainability and easier debugging.
	- Once these foundational changes are complete, we will resume and finish the folder detection feature.

2. **Core tagging system for asset categorization (COMPLETED):**
	- Clear definition of asset categories using configuration files. ([issue](docs/issues/0010-core-tagging-feature/))
	- Automatic tags to inform users about categorized and uncategorized assets. ([issue](docs/issues/0010-core-tagging-feature/))
	- Conflict tags when categorization issues are detected. ([issue](docs/issues/0010-core-tagging-feature/))

3. **Refactor and modularize codebase:**
	Split the main script into smaller, maintainable modules. Evaluate moving configuration out of code files (users have requested a non-code config solution).
4. **Similar photo detection:**
	Implement logic to detect duplicate or near-duplicate photos (e.g., WhatsApp copies) using available metadata.
5. **Date correction for assets:**
	Many photos have incorrect dates. Analyze strategies to recover the true date, e.g., from folder names or from similar/identical photos with correct dates.
6. **Containerization:**
	Some users have requested a containerized version of this application. This is under consideration. See: https://github.com/txemi/immich-autotag/issues/1

## 1.2. Next Integrity Rules to Implement

The following are integrity rules, which ensure that the tagging and classification remain consistent and logical. Other types of rules (e.g., automation, enrichment, or workflow rules) may be added in future sections as the project evolves.


1. **Rule:** Photos with recognized faces should not be tagged as `meme` or `adult meme`.
2. **Rule:** Photos with recognized faces should belong to an event album.
3. **Rule:** Photos belonging to specific groups of albums (e.g., people groups, family trees) should not be tagged as `meme` or `adult meme`. These album groups should be definable by pattern.




## 1.3. Automation and Utilities


1. Automatically create albums based on existing regular folder structures (e.g., import folder hierarchies as albums).
2. Assist in the detection and management of duplicate folders or files within the photo library.
3. Provide an official Docker image for easy deployment and usage (requested by users).




## 1.4. Integration Ideas

1. Integrate with external AI-based classification systems for enhanced tagging.

---

*Last updated: 2025-12-21*
