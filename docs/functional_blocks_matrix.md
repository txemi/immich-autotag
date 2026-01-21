
# Functional Blocks Matrix

This table lists the main functional blocks (features) of Immich AutoTag, their status, and links to related issues/tasks. It serves as a reference for developers and for grouping changes in the changelog.


| ID      | Functional Block                        | Type         | Brief Description                                                      | Status     | Related Issues/Tasks                                                                 | Version |
|---------|-----------------------------------------|--------------|------------------------------------------------------------------------|------------|--------------------------------------------------------------------------------------|---------|
| FB-001  | Automatic album creation and assignment | User-facing  | Create and assign albums based on detected duplicates or folders        | Complete   | [0016-auto-album-creation/readme.md](../issues/0016-auto-album-creation/readme.md)            |         |
| FB-002  | Rule-based classification engine        | User-facing  | Automatic classification using tag and album name patterns              | Complete   | [0017-rules-tag-album-combination/readme.md](../issues/0017-rules-tag-album-combination/readme.md) |         |
| FB-003  | Permission management                   | User-facing  | Automatic album permission assignment by group and rules                | In progress| [0018-user-group-policies/readme.md](../issues/0018-user-group-policies/readme.md)            |         |
| FB-004  | Automatic date correction               | User-facing  | Fix asset dates using duplicates or filenames                           | Complete   | [0019-album-date-consistency-config/readme.md](../issues/0019-album-date-consistency-config/readme.md) |         |
| FB-005  | Global filtering                        | User-facing  | Include/exclude assets, albums, or tags using filters                   | Complete   | [0005-filter-assets/](../issues/0005-filter-assets/)                                   |         |
| FB-006  | Date mismatch tagging                   | User-facing  | Detect and tag assets with inconsistent dates                           | In progress| [0019-album-date-consistency-config/readme.md](../issues/0019-album-date-consistency-config/readme.md) |         |
| FB-007  | Modification and statistics logs        | User-facing  | Generate modification and statistics reports                            | Complete   | [0008-statistics-checkpoint/](../issues/0008-statistics-checkpoint/)                  |         |
| FB-008  | Continuous or scheduled tagging         | User-facing  | Script for continuous or scheduled tagging/classification (cron/docker) | Complete   | [0021-profiling-performance/readme.md](../issues/0021-profiling-performance/readme.md)         |         |
| FB-009  | Batch tag/album conversions             | User-facing  | Apply batch changes to tags or albums                                   | In progress|                                                                                      |         |
| FB-010  | Duplicate management engine             | Internal     | Internal engine for detecting and managing duplicate assets, used by other features | Complete   | [0003-duplicates-management/](../issues/0003-duplicates-management/)                  |         |

> This table is a first version and should be updated as the project evolves. Issue links can be expanded or corrected as needed.
