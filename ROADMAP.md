# 1. Roadmap: Immich AutoTag

This document lists upcoming rules, features, and improvements planned for the Immich AutoTag project. Please update this file as new ideas or requirements arise.


## 1.1. Upcoming Features (to be prioritized)

- **Album detection and creation from folders:**
	If an album does not exist, implement logic to infer or create it based on folder structure.

- **Refactor and modularize codebase:**
	Split the main script into smaller, maintainable modules. Evaluate moving configuration out of code files (users have requested a non-code config solution).

- **Similar photo detection:**
	Implement logic to detect duplicate or near-duplicate photos (e.g., WhatsApp copies) using available metadata.

- **Date correction for assets:**
	Many photos have incorrect dates. Analyze strategies to recover the true date, e.g., from folder names or from similar/identical photos with correct dates.

- **Containerization:**
	Some users have requested a containerized version of this application. This is under consideration. See: https://github.com/txemi/immich-autotag/issues/1
---

*Note: These items will be organized and prioritized in a future update.*

## 1.2. Next Integrity Rules to Implement

The following are integrity rules, which ensure that the tagging and classification remain consistent and logical. Other types of rules (e.g., automation, enrichment, or workflow rules) may be added in future sections as the project evolves.

2. **Rule:** Photos with recognized faces should belong to an event album.
1. **Rule:** Photos with recognized faces should not be tagged as `meme` or `adult meme`.
3. **Rule:** Photos belonging to specific groups of albums (e.g., people groups, family trees) should not be tagged as `meme` or `adult meme`. These album groups should be definable by pattern.




## 1.3. Automation and Utilities

1. Automatically create albums based on existing regular folder structures (e.g., import folder hierarchies as albums).
2. Assist in the detection and management of duplicate folders or files within the photo library.
3. Provide an official Docker image for easy deployment and usage (requested by users).




## 1.4. Integration Ideas

1. Integrate with external AI-based classification systems for enhanced tagging.

---

*Last updated: 2025-12-21*
