# Migration Plan: Adopt Local Issue System

## 1. Review and Classification of Existing Docs
| File/Folder                                      | Action/Target Issue Folder                        | Notes |
|--------------------------------------------------|---------------------------------------------------|-------|
| about_openapi.md                                 | Leave in docs/ (general)                          | General API info |
| duplicates_management_plan.md                    | Move to 0003-duplicates-management/design/         | Specific to duplicates feature |
| feature-album-detection-from-folders/            | Move contents to 0004-album-detection/design/      | Feature-specific |
| feature-filter-assets-config.md                  | Move to 0005-filter-assets/design/                 | Feature-specific |
| immich_issue_orphan_albums.md                    | Move to 0006-orphan-albums/design/                 | Feature-specific |
| refactor_process_single_asset.md                 | Move to 0007-refactor-process-single-asset/design/ | Refactor-specific |
| statistics_checkpoint_design.md                  | Move to 0008-statistics-checkpoint/design/         | Design-specific |
| statistics_checkpoint_todo.md                    | Move to 0008-statistics-checkpoint/design/         | Task-specific |

## 2. Steps for Adoption
1. Create new issue folders for each feature/refactor as listed above.
2. Move each document to its corresponding `design/` subfolder.
3. Update `docs/issues/registry.md` with new issues and their status.
4. Update `CHANGELOG.md` and `ROADMAP.md` to link to the new issue folders and docs.
5. Remove or archive obsolete docs if found during review.
6. Announce the new system in project documentation.

## 3. Checklist
- [ ] All files moved as per table
- [ ] All links updated
- [ ] Registry updated
- [ ] Announcement made
