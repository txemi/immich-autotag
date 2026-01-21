
# Functional Blocks Matrix

This table lists the main functional blocks (features) of Immich AutoTag, their status, and links to related issues/tasks. It serves as a reference for developers and for grouping changes in the changelog.


| Functional Block                        | Brief Description                                                      | Status     | Related Issues/Tasks                                                                 | Version |
|-----------------------------------------|------------------------------------------------------------------------|------------|--------------------------------------------------------------------------------------|---------|
| Automatic album creation and assignment | Create and assign albums based on detected duplicates or folders        | Complete   | [0016-auto-album-creation](../issues/0016-auto-album-creation/readme.md)            |         |
| Rule-based classification engine        | Automatic classification using tag and album name patterns              | Complete   | [0017-rules-tag-album-combination](../issues/0017-rules-tag-album-combination/readme.md) |         |
| Permission management                   | Automatic album permission assignment by group and rules                | In progress| [0018-user-group-policies](../issues/0018-user-group-policies/readme.md)            |         |
| Automatic date correction               | Fix asset dates using duplicates or filenames                           | Complete   | [0019-album-date-consistency-config](../issues/0019-album-date-consistency-config/readme.md) |         |
| Global filtering                        | Include/exclude assets, albums, or tags using filters                   | Complete   | [0005-filter-assets](../issues/0005-filter-assets/)                                   |         |
| Date mismatch tagging                   | Detect and tag assets with inconsistent dates                           | In progress| [0019-album-date-consistency-config](../issues/0019-album-date-consistency-config/readme.md) |         |
| Modification and statistics logs        | Generate modification and statistics reports                            | Complete   | [0008-statistics-checkpoint](../issues/0008-statistics-checkpoint/)                  |         |
| Continuous or scheduled tagging         | Script for continuous or scheduled tagging/classification (cron/docker) | Complete   | [0021-profiling-performance](../issues/0021-profiling-performance/readme.md)         |         |
| Batch tag/album conversions             | Apply batch changes to tags or albums                                   | In progress| [0022-batch-tag-album-conversions](../issues/0022-batch-tag-album-conversions/)      |         |

> This table is a first version and should be updated as the project evolves. Issue links can be expanded or corrected as needed.
