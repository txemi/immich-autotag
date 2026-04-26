# 004 · Temp-unclassified albums incorrectly created for classified assets

## Purpose

Bug: assets already classified (with `autotag_output_*` tags or processed by a conversion that removes `autotag_input_meme`) are being placed into `YYYY-MM-DD-autotag-temp-unclassified` albums.

## Scope

- **What's included:** classification check before temp-album assignment; interaction between conversion phase and classification phase
- **What's excluded:** conversion logic itself, duplicate-name album resolution

## Status

Identified — **Not fixed**. Observed live in Jenkins on `fix/conversion-album-move` branch (build #13, 2026-04-25).

## Cross-References

- **Parent subtask:** [001-create-temporary-albums](../001-create-temporary-albums/)
- **Related subtask:** [002-cleanup-from-temporary-albums](../002-cleanup-from-temporary-albums/)
- **Key source file:** `immich_autotag/assets/albums/temporary_manager/create_if_missing_classification.py`
- **Classification routing:** `immich_autotag/assets/albums/analyze_and_assign_album/_handle_unclassified_asset.py`

## Notes

See `ai-context.md` for full incident diagnosis and proposed fixes.

---

*Last updated: 2026-04-25*
