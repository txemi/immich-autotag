# AI Context · 004 · Temp-unclassified albums for already-classified assets

Last verified: 2026-04-26

---

## Current state

Root cause identified. **Fix exists locally but has NOT been pushed.** Observation mode active.

### Why the fix is on hold

The anomalous temp albums were observed while two Jenkins builds were running in parallel.
Parallel execution is a plausible alternative explanation for the same symptoms:
- Two builds with independent album-map snapshots can disagree on asset state
- One build removes a tag; the other still sees the asset as unclassified and creates a temp album

From 2026-04-26, only one sequential build runs at a time. The next few runs will determine
whether temp albums for already-classified assets still appear without the code fix.

**Decision rule:**
- If anomalous temp albums reappear in sequential runs → the code fix is needed, push it
- If they do not reappear → parallel execution was the cause; close this issue without a code change

The local fix (in `conversion_wrapper.py` and `destination_wrapper.py`) should not be pushed
until this observation period confirms it is necessary.

---

## Incident observation

On 2026-04-25, an Immich album `2016-10-20-autotag-temp-unclassified` was observed in the UI containing meme-content assets from October 2016. These assets should never be placed in a temp album.

At the time, two Jenkins builds were running simultaneously on `fix/conversion-album-move`:

| Build | Started | Status at discovery |
|---|---|---|
| [#4](http://ubuntu20jenkins.ad3.lab:8080/job/immich-autotag/job/fix%252Fconversion-album-move/4/) | 2026-04-24 12:34 | Conversion phase, ~78%, removing `autotag_output_unknown` |
| [#13](http://ubuntu20jenkins.ad3.lab:8080/job/immich-autotag/job/fix%252Fconversion-album-move/13/) | 2026-04-25 19:54 | Classification phase, ~9.5%, active `autotag_input_meme` removals |

**Both builds were stopped.** On 2026-04-26 the second Jenkins node was taken down to prevent parallel runs and make future runs easier to diagnose.

---

## Root cause (confirmed from code + log analysis)

### The conversion config (from `user_config_template.py`)

```python
Conversion(
    source=ClassificationRule(tag_names=["meme", "autotag_input_meme"]),
    destination=Destination(album_names=["autotag_input_meme"]),
    mode=ConversionMode.MOVE,
)
```

This conversion should: find assets with the tag → add to `autotag_input_meme` album → remove tag.

### The classification rule (from `user_config_template.py`)

```python
ClassificationRule(
    tag_names=["meme", "autotag_input_meme"],
    album_name_patterns=["^autotag_input_meme$"],
)
```

After a successful conversion, the asset is in the album → this rule matches → `CLASSIFIED`. The design is sound.

### Where it breaks: `destination_wrapper.py` + `conversion_wrapper.py`

**In `destination_wrapper.apply_action()`**, when the destination album doesn't exist in the collection:

```python
album_wrapper = albums_collection.find_first_album_with_name(album_name)
if album_wrapper:
    entry = album_wrapper.add_asset(...)
else:
    pass  # ← silent skip, no log, no error
```

**In `conversion_wrapper.apply_to_asset()`**, `remove_matches()` is called unconditionally after `apply_action()`:

```python
changes = changes.extend(result_action.apply_action(asset_wrapper))  # may silently fail
if self.conversion.mode == ConversionMode.MOVE and match_result is not None:
    self.get_source_wrapper().remove_matches(...)  # ← ALWAYS runs, even if apply_action did nothing
```

### The failure sequence

1. First run on this branch: album `autotag_input_meme` doesn't exist in Immich yet
2. `apply_action()`: `find_first_album_with_name("autotag_input_meme")` → `None` → silent skip
3. `remove_matches()`: removes tag `autotag_input_meme` from asset — **unconditionally**
4. Asset state: no tag, not in album → `ClassificationStatus.UNCLASSIFIED`
5. `create_album_if_missing_classification()` → creates `2016-10-20-autotag-temp-unclassified`

The album `autotag_input_meme` was created later (when processing other assets or runs), but the 2016 batch assets had already lost their classification signal and were trapped in temp albums.

### Build #13 startup log confirms prior damage

Build #13's startup showed **dozens of duplicate temp-unclassified albums** from March–April 2017 being deleted at init:
```
[WARNING] Album name conflict: '2017-03-30-autotag-temp-unclassified' already exists...
[PROGRESS] [DELETE_ALBUM] Album '2017-03-30-autotag-temp-unclassified' deleted.
```
These duplicates came from multiple parallel runs all creating the same temp albums concurrently — confirming the bug triggered at scale.

---

## Fix implemented (pending review)

### Bug 1 — `conversion_wrapper.py`

**Before**: `remove_matches()` always runs after `apply_action()`, even when album assignment was skipped.

**After**: source tags are only removed if all destination albums are confirmed to be in the asset's album membership after the action. If any destination album is missing, a WARNING is logged and the source tag is preserved.

Key logic:
```python
current_album_names = set(asset_wrapper.get_album_names())
all_destinations_resolved = all(
    album_name in current_album_names for album_name in destination_albums
)
if all_destinations_resolved:
    self.get_source_wrapper().remove_matches(...)
else:
    log("[CONVERSION] Skipping source removal: destination album not resolved ...", WARNING)
```

This works because `album_response_wrapper.add_asset()` calls `update_asset_to_albums_map_for_asset()` on success, so `get_album_names()` reflects the new state immediately. Assets already in the album (no API call needed) also pass the check correctly.

### Bug 2 — `destination_wrapper.py`

**Before**: silent `pass` when destination album not found.

**After**: ERROR log that makes the problem visible in Jenkins output.

---

## Key files

| File | Role |
|---|---|
| `immich_autotag/conversions/conversion_wrapper.py` | **Fixed** — conditional `remove_matches()` |
| `immich_autotag/conversions/destination_wrapper.py` | **Fixed** — ERROR log when album not found |
| `immich_autotag/assets/albums/temporary_manager/create_if_missing_classification.py` | Downstream victim, not changed |
| `immich_autotag/assets/albums/analyze_and_assign_album/_handle_unclassified_asset.py` | Downstream victim, not changed |
| `immich_autotag/config/user_config_template.py` | Shows conversion + classification rule design |

---

## Data remediation needed (not yet done)

The assets trapped in existing temp albums (e.g. `2016-10-20-autotag-temp-unclassified`) have lost their classification signal:
- No `autotag_input_meme` tag
- Not in `autotag_input_meme` album

Options:
- **Manual**: in Immich UI, add those assets to the `autotag_input_meme` album → next run will classify them correctly and clean the temp album
- **Run with filter**: run autotag with `filter_in: album_name_patterns=["*-autotag-temp-unclassified"]` after re-tagging

---

## Next steps

1. Review the fix locally (diff in `conversion_wrapper.py` and `destination_wrapper.py`)
2. Run on a small batch to confirm the WARNING log fires when expected and no temp albums are created
3. Perform data remediation on the existing temp albums with meme content
4. Consider adding a test: mock a conversion where destination album doesn't exist → assert source tag is preserved

---
