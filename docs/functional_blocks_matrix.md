---
uuid: ccb2c8bd-b14a-447f-a9d6-037fd14c5592
---


# Functional Blocks Matrix

This table lists the main functional blocks (features) of Immich AutoTag, their status, and links to related issues/tasks. It serves as a reference for developers and for grouping changes in the changelog.

**Last updated:** 2026-02-01 (Updated to map to v2.0 issue system - 0020+)

| ID      | Functional Block                        | Type         | Brief Description                                                      | Status     | Related Issues/Tasks                                                                 |
|---------|-----------------------------------------|--------------|------------------------------------------------------------------------|------------|--------------------------------------------------------------------------------------|
| FB-001  | Automatic album creation and assignment | User-facing  | Create and assign albums based on detected duplicates or folders        | In progress| [0024-album-features](issues/0024-album-features) <!-- uuid: 186d6b69-5c4f-45d0-9b73-594ce5d73ff5 --> · [0029-core-logic](issues/0029-core-logic) <!-- uuid: 127716d5-d27b-4867-843e-91b2a8574198 --> |
| FB-002  | Rule-based classification engine        | User-facing  | Automatic classification using tag and album name patterns              | In progress| [0030-rule-engine](issues/0030-rule-engine) <!-- uuid: e65d2381-2ab0-4d9f-8a15-bc505bb7bfe2 -->                          |
| FB-003  | Permission management                   | User-facing  | Automatic album permission assignment by group and rules                | In progress| [0032-user-management-and-access-control-feature](issues/0032-user-management-and-access-control-feature) <!-- uuid: f58163b4-d269-449f-bc3d-53184168f084 --> |
| FB-004  | Automatic date correction               | User-facing  | Fix asset dates using duplicates or filenames                           | In progress| [0027-config-feature](issues/0027-config-feature) <!-- uuid: e8514991-5f8c-4a9f-86e9-74b064c2148a --> · [0025-asset-features](issues/0025-asset-features) <!-- uuid: cd8b3fa4-1215-4045-933b-3cbd7d35cb8b --> |
| FB-005  | Global filtering                        | User-facing  | Include/exclude assets, albums, or tags using filters                   | In progress| [0025-asset-features](issues/0025-asset-features) <!-- uuid: cd8b3fa4-1215-4045-933b-3cbd7d35cb8b --> · [0029-core-logic](issues/0029-core-logic) <!-- uuid: 127716d5-d27b-4867-843e-91b2a8574198 --> |
| FB-006  | Date mismatch tagging                   | User-facing  | Detect and tag assets with inconsistent dates                           | In progress| [0026-statistics-feature](issues/0026-statistics-feature) <!-- uuid: 69055f5c-bb82-4eae-8fac-1c1e0d2309b2 --> · [0025-asset-features](issues/0025-asset-features) <!-- uuid: cd8b3fa4-1215-4045-933b-3cbd7d35cb8b --> |
| FB-007  | Modification and statistics logs        | User-facing  | Generate modification and statistics reports                            | In progress| [0026-statistics-feature](issues/0026-statistics-feature) <!-- uuid: 69055f5c-bb82-4eae-8fac-1c1e0d2309b2 -->            |
| FB-008  | Continuous or scheduled tagging         | User-facing  | Script for continuous or scheduled tagging/classification (cron/docker) | In progress| [0031-cicd](issues/0031-cicd) <!-- uuid: 0443c418-37e9-4a30-be7a-ec1286afb322 --> · [0027-config-feature](issues/0027-config-feature) <!-- uuid: e8514991-5f8c-4a9f-86e9-74b064c2148a --> · [0021-profiling-performance](issues/0021-profiling-performance) <!-- uuid: 679d0035-a83a-4ba6-8631-f9500db5eedd --> |
| FB-009  | Batch tag/album conversions             | User-facing  | Apply batch changes to tags or albums                                   | Proposed   | [0030-rule-engine](issues/0030-rule-engine) <!-- uuid: e65d2381-2ab0-4d9f-8a15-bc505bb7bfe2 --> · [0024-album-features](issues/0024-album-features) <!-- uuid: 186d6b69-5c4f-45d0-9b73-594ce5d73ff5 --> |
| FB-010  | Duplicate management engine             | Internal     | Internal engine for detecting and managing duplicate assets, used by other features | In progress| [0029-core-logic](issues/0029-core-logic) <!-- uuid: 127716d5-d27b-4867-843e-91b2a8574198 -->                            |
| FB-011  | Community & Collaboration               | Internal     | Community outreach, documentation, and collaboration                    | Ongoing    | [0033-community](issues/0033-community) <!-- uuid: 860ef7ae-2b08-402b-b076-a26c37e8007f --> · [0020-docs-track-branch](issues/0034-branching-and-devel-workflow/subtasks/0020-docs-track-branch) <!-- uuid: 39934be1-5b1b-442b-a8f0-6ea2a86c2455 --> · [0034-branching-and-devel-workflow](issues/0034-branching-and-devel-workflow) <!-- uuid: 252d0f15-e793-4594-b670-dc099ac8e60a --> |
| FB-012  | Infrastructure & Publishing             | Internal     | CI/CD, publishing, performance profiling, and project infrastructure    | Ongoing    | [0031-cicd](issues/0031-cicd) <!-- uuid: 0443c418-37e9-4a30-be7a-ec1286afb322 --> · [0022-release-preparation](issues/0022-release-preparation) <!-- uuid: be57ab2c-6b18-4517-a6bf-0bd09265f08c --> · [0021-profiling-performance](issues/0021-profiling-performance) <!-- uuid: 679d0035-a83a-4ba6-8631-f9500db5eedd --> |

---

## Notes

- This table maps functional blocks to active issues in the v2.0 issue system (issues 0020+).
- Legacy issues (0001-0019) have been archived and consolidated into the current thematic organization.
- Issue links use the naming convention `NNNN-descriptive-slug` for consistency with the registry.
- See [Issue Registry](./issues/registry.md) <!-- uuid: 805cc158-bb61-497d-96dd-7a6efece6acf --> for the complete list of active and legacy issues.
- Status indicates current implementation progress; "In progress" may include completed features with ongoing refinement.
