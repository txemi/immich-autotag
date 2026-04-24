# Task brief: Meme album consolidation + MOVE conversion bug fix

## Goal

Consolidate date-based meme albums (e.g. `2020-04-29-memes`) into a single canonical album (`autotag_input_meme`). A structural bug in the conversion engine was found and must be fixed first.

---

## Current state

### Private config repo (`~/.config/immich_autotag`) — ALREADY COMMITTED

The two existing conversion rules were updated to add `album_name_patterns` as an additional source criterion (OR with the existing tag names):

```python
# Conversion 1: memes
source=ClassificationRule(
    tag_names=['meme', 'autotag_input_meme'],
    album_name_patterns=[r"^\d{4}(-\d{2}(-\d{2})?)?-memes$"],  # NEW
),
destination=Destination(album_names=['autotag_input_meme']),
mode=ConversionMode.MOVE,

# Conversion 2: adult_memes (analogous)
source=ClassificationRule(
    tag_names=['adult_meme', 'autotag_input_adult_meme'],
    album_name_patterns=[r"^\d{4}(-\d{2}(-\d{2})?)?-adult_memes$"],  # NEW
),
destination=Destination(album_names=['autotag_input_adult_meme']),
mode=ConversionMode.MOVE,
```

### Public repo — UNCOMMITTED CHANGES (branch `improvement/claude-code-setup`)

Three files modified. Two are fixes required for the consolidation to work correctly:

**1. `immich_autotag/albums/album/album_response_wrapper.py`**
Added `remove_asset_for_conversion()` — same as `remove_asset()` but without the guard that restricts removal to temporary or duplicate albums. Required because date-based meme albums are regular albums.

**2. `immich_autotag/classification/classification_rule_wrapper.py`**
Implemented the album removal loop in `remove_matches()` that was commented out with a `...` placeholder. Uses the new `remove_asset_for_conversion()` method.

**3. `immich_autotag/conversions/destination_wrapper.py`**
This file had pre-existing changes before this session (not introduced by this task).

---

## Bug still to fix (NOT applied yet)

In `conversion_wrapper.py`, method `apply_to_asset()`, the MOVE unconditionally removes the source album even if the destination addition failed silently:

```python
# Current code (BROKEN):
changes = changes.extend(result_action.apply_action(asset_wrapper))  # can fail silently
if self.conversion.mode == ConversionMode.MOVE:
    self.get_source_wrapper().remove_matches(...)  # runs unconditionally
```

The silent failure happens in `destination_wrapper.apply_action()` when the destination album does not exist (`else: pass`) or an exception is swallowed (`except Exception: pass`).

**Proposed fix for `conversion_wrapper.py`:**

```python
if source_matched:
    result_action = self.get_destination_wrapper()
    changes = changes.extend(result_action.apply_action(asset_wrapper))
    if self.conversion.mode == ConversionMode.MOVE and match_result is not None:
        dest_albums = result_action.get_album_names()
        current_albums = set(asset_wrapper.get_album_names())
        dest_albums_reached = all(a in current_albums for a in dest_albums)
        if not dest_albums or dest_albums_reached:
            self.get_source_wrapper().remove_matches(asset_wrapper, match_result)
```

Logic: only remove the source album if the asset is confirmed present in all destination albums (either just added, or already there). If the destination did not exist or the addition failed, leave the asset where it was.

---

## Steps to continue in the new workspace

1. **Create a new branch** from `improvement/claude-code-setup` (or from `main` for a clean base):
   ```bash
   git checkout -b fix/conversion-album-move
   ```

2. **Carry over the existing changes** in `album_response_wrapper.py` and `classification_rule_wrapper.py` (already in the working tree if cloned from the same state, or cherry-pick if needed).

3. **Apply the fix to `conversion_wrapper.py`** as described above.

4. **Run the Quality Gate**:
   ```bash
   bash scripts/devtools/quality_gate_py/venv_launcher.sh --level=STANDARD --mode=CHECK
   ```

5. **Test locally** using `config1file.py` pointing to an asset in a `YYYY-MM-DD-memes` album. Verify the asset appears in `autotag_input_meme` and is removed from the date album.

6. **Show diff → wait for explicit user confirmation → commit.**

7. Once working: run with the full `config.py` (confirm with user first — this operates on real Immich data).

---

## Relevant architectural notes

- `ClassificationRule` uses **OR** logic between `tag_names` and `album_name_patterns`.
- Conversions run in **two phases**: `apply_conversions_to_all_assets_early` (all assets at startup) and again per asset in the main processing loop. The bug was relevant in both phases.
- `album_response_wrapper.remove_asset()` had a guard `_ensure_removal_allowed()` blocking removal from regular albums — hence the new `remove_asset_for_conversion()`.
- The private config repo may reference the public repo, but **never the other way around**.
- **Never commit without showing the diff and waiting for explicit user confirmation.**
