
# Functional Blocks Matrix

This table lists the main functional blocks (features) of Immich AutoTag, their status, and links to related issues/tasks. It serves as a reference for developers and for grouping changes in the changelog.

**Last updated:** 2026-02-01 (Updated to map to v2.0 issue system - 0020+)

| ID      | Functional Block                        | Type         | Brief Description                                                      | Status     | Related Issues/Tasks                                                                 |
|---------|-----------------------------------------|--------------|------------------------------------------------------------------------|------------|--------------------------------------------------------------------------------------|
| FB-001  | Automatic album creation and assignment | User-facing  | Create and assign albums based on detected duplicates or folders        | In progress| [0024-album-features](../issues/0024-album-features/) · [0029-core-logic](../issues/0029-core-logic/) |
| FB-002  | Rule-based classification engine        | User-facing  | Automatic classification using tag and album name patterns              | In progress| [0030-rule-engine](../issues/0030-rule-engine/)                          |
| FB-003  | Permission management                   | User-facing  | Automatic album permission assignment by group and rules                | In progress| [0032-user-management-and-access-control-feature](../issues/0032-user-management-and-access-control-feature/) |
| FB-004  | Automatic date correction               | User-facing  | Fix asset dates using duplicates or filenames                           | In progress| [0027-config-feature](../issues/0027-config-feature/) · [0025-asset-features](../issues/0025-asset-features/) |
| FB-005  | Global filtering                        | User-facing  | Include/exclude assets, albums, or tags using filters                   | In progress| [0025-asset-features](../issues/0025-asset-features/) · [0029-core-logic](../issues/0029-core-logic/) |
| FB-006  | Date mismatch tagging                   | User-facing  | Detect and tag assets with inconsistent dates                           | In progress| [0026-statistics-feature](../issues/0026-statistics-feature/) · [0025-asset-features](../issues/0025-asset-features/) |
| FB-007  | Modification and statistics logs        | User-facing  | Generate modification and statistics reports                            | In progress| [0026-statistics-feature](../issues/0026-statistics-feature/)            |
| FB-008  | Continuous or scheduled tagging         | User-facing  | Script for continuous or scheduled tagging/classification (cron/docker) | In progress| [0031-cicd](../issues/0031-cicd/) · [0027-config-feature](../issues/0027-config-feature/) · [0021-profiling-performance](../issues/0021-profiling-performance/) |
| FB-009  | Batch tag/album conversions             | User-facing  | Apply batch changes to tags or albums                                   | Proposed   | [0030-rule-engine](../issues/0030-rule-engine/) · [0024-album-features](../issues/0024-album-features/) |
| FB-010  | Duplicate management engine             | Internal     | Internal engine for detecting and managing duplicate assets, used by other features | In progress| [0029-core-logic](../issues/0029-core-logic/)                            |
| FB-011  | Community & Collaboration               | Internal     | Community outreach, documentation, and collaboration                    | Ongoing    | [0033-community](../issues/0033-community/) · [0020-docs-track-branch](../issues/0020-docs-track-branch/) · [0034-branching-and-devel-workflow](../issues/0034-branching-and-devel-workflow/) |
| FB-012  | Infrastructure & Publishing             | Internal     | CI/CD, publishing, performance profiling, and project infrastructure    | Ongoing    | [0031-cicd](../issues/0031-cicd/) · [0022-release-preparation](../issues/0022-release-preparation/) · [0021-profiling-performance](../issues/0021-profiling-performance/) |

---

## Notes

- This table maps functional blocks to active issues in the v2.0 issue system (issues 0020+).
- Legacy issues (0001-0019) have been archived and consolidated into the current thematic organization.
- Issue links use the naming convention `NNNN-descriptive-slug` for consistency with the registry.
- See [Issue Registry](./issues/registry.md) for the complete list of active and legacy issues.
- Status indicates current implementation progress; "In progress" may include completed features with ongoing refinement.
