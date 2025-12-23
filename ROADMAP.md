# 1. Roadmap: Immich AutoTag

This document lists upcoming rules, features, and improvements planned for the Immich AutoTag project. Please update this file as new ideas or requirements arise.

Note: This roadmap lists upcoming features in order of priority, based on a subjective assessment of what delivers the most value and quick wins for the project.


## 1.1. Upcoming Features (to be prioritized)

1. **Album detection and creation from folders:**
	If an album does not exist, implement logic to infer or create it based on folder structure.
    
	[See detailed design document →](docs/feature-album-detection-from-folders.md)
2. **Refactor and modularize codebase:**
	Split the main script into smaller, maintainable modules. Evaluate moving configuration out of code files (users have requested a non-code config solution).
3. **Similar photo detection:**
	Implement logic to detect duplicate or near-duplicate photos (e.g., WhatsApp copies) using available metadata.
4. **Date correction for assets:**
	Many photos have incorrect dates. Analyze strategies to recover the true date, e.g., from folder names or from similar/identical photos with correct dates.
5. **Containerization:**
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
