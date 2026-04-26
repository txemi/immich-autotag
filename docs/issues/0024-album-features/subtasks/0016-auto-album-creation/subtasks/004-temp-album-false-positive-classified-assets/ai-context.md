# AI Context · 004 · Temp-unclassified albums for already-classified assets

Last verified: 2026-04-25

---

## Current state

Bug identified live. **Not fixed.** Active on branch `fix/conversion-album-move`.

---

## Incident observation

On 2026-04-25, an Immich album `2016-10-20-autotag-temp-unclassified` was observed in the UI containing meme-content assets from October 2016. These assets had been classified as memes long ago (had `autotag_input_meme` or `autotag_output_meme` tags) and should never be placed in a temp album.

---

## Active Jenkins builds at time of discovery

Two builds were running simultaneously on `fix/conversion-album-move`:

| Build | Started | Progress | Total assets | Role |
|---|---|---|---|---|
| [#4](http://ubuntu20jenkins.ad3.lab:8080/job/immich-autotag/job/fix%252Fconversion-album-move/4/) | 2026-04-24 12:34 | ~78% | 403,736 | Full conversion pass, removing `autotag_output_unknown` |
| [#13](http://ubuntu20jenkins.ad3.lab:8080/job/immich-autotag/job/fix%252Fconversion-album-move/13/) | 2026-04-25 19:54 | ~9.5% | 30,000 (batch) | Filtered batch; actively removing `autotag_input_meme`, many classification conflicts |

**Build #13 is the likely creator** of the bad temp albums. Its logs show:
```
[PROGRESS] [REMOVE_TAG_FROM_ASSET] Tag 'autotag_input_meme' removed from asset bc614388...
[ERROR] [ALBUM ASSIGNMENT] Asset '...' matched 2 classification rules. Classification conflict
```
Build #4 was in the conversion phase removing `autotag_output_unknown` and not in classification territory at that moment.

---

## Root cause analysis

The pipeline in this branch runs:
1. `apply_conversions_to_all_assets()` — conversions detect `autotag_input_meme`, move asset to meme album, remove `autotag_input_meme` tag
2. `process_assets_or_filtered()` — classification phase runs on the same assets

After step 1, the asset no longer has `autotag_input_meme`. In step 2:
- `ClassificationRuleSet.matching_rules(asset_wrapper)` checks current tags against rule definitions
- The meme rule matches on `autotag_input_meme` — now absent → **no match**
- `ClassificationStatus` → `UNCLASSIFIED`
- `_handle_unclassified_asset()` → `create_album_if_missing_classification()` → temp album created

The safety check in `create_if_missing_classification.py` (line 60) only blocks the flow if a rule matches. It does **not** check whether the asset already has `autotag_output_*` tags or is already in a classified album.

### Secondary problem

Build #13 also shows frequent `matched 2 classification rules` errors — some assets match both the meme rule and another rule simultaneously. This is a separate classification-conflict issue but may be contributing to inconsistent state.

---

## Key files

| File | Relevance |
|---|---|
| `immich_autotag/assets/albums/temporary_manager/create_if_missing_classification.py` | Where the temp album assignment happens; line 60 is the classification status check |
| `immich_autotag/assets/albums/analyze_and_assign_album/_handle_unclassified_asset.py` | Routes UNCLASSIFIED assets to temp album logic |
| `immich_autotag/assets/albums/analyze_and_assign_album/_analyze_and_assign_album.py` | Top-level dispatcher by ClassificationStatus |
| `immich_autotag/classification/classification_rule_wrapper.py` | Rule matching — only checks `tag_names` in rule definition, not output tags |
| `immich_autotag/assets/asset_response_wrapper.py` | `apply_tag_conversions()` — conversion execution |

---

## Proposed fixes (not implemented)

**Option A — skip if asset has any `autotag_output_*` tag** (recommended for quick fix):
In `create_album_if_missing_classification`, before the album assignment, check if the asset has any tag starting with `autotag_output_`. If yes, skip temp album creation. These tags are written by autotag and indicate a prior classification pass completed successfully.

**Option B — recognise `autotag_output_*` as a classification signal** (more correct long-term):
In `ClassificationRuleWrapper` or `ClassificationRuleSet`, extend the matching logic so that if an asset has a tag `autotag_output_X` that corresponds to an existing rule, it is treated as `CLASSIFIED`. This would also fix the case where the input tag was lost by accident.

**Option C — prevent conversion from removing the input tag until after classification** (architectural):
Decouple the conversion phase from the classification phase so that input tags are preserved during the classification step, then cleaned up afterward. Higher risk/effort.

---

## Next steps (to pick up from here)

1. Read `create_if_missing_classification.py` (lines 40–63) and `_handle_unclassified_asset.py` to confirm the exact call path
2. Decide between Option A (fast) or Option B (correct)
3. Implement + add a test that covers: asset with `autotag_output_meme` and no `autotag_input_meme` must not get a temp album
4. Confirm Build #13 has finished and check if `2016-10-20-autotag-temp-unclassified` was populated further or cleaned up
5. Manually delete or reassign any incorrectly created temp-unclassified albums containing meme assets

---
