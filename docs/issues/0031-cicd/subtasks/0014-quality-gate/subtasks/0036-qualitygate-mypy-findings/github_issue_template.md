Title: CI: mypy failures due to immich-client DTO changes (assets/id)

Body

Summary
- The Jenkins Quality Gate `check_mypy` is failing with typing errors that appear to be caused by changes or discrepancies in the `immich-client` generated DTOs. These failures block CI for branch `fix/immich-client-dto-compat` and may be caused by the server/client changing the shape/types of Album/User DTOs (notably `id` and `assets`).

Why this matters
Why this matters
- These are not only static-type warnings: they lead to runtime failures (see backtrace) and indicate a possible change in the API contract between server and generated client DTOs. We do NOT want temporary ignores; we want to understand the new API surface and implement a correct, long-term fix (adapter/wrapper/tests or updated codegen). This issue coordinates that investigation.

Branch and related artifacts
- Branch created for investigation and minimal fixes: `fix/immich-client-dto-compat`
- LLM-ready analysis and logs: docs/issues/0031-cicd/subtasks/0014-quality-gate/subtasks/0036-qualitygate-mypy-findings/
  - analysis_llm_report.md
  - mypy_findings.md
  - backtrace.md
  - README.md

Observed CI findings (summary)
- mypy reported 5 errors (see attached `mypy_findings.md`). Examples:
  - `BaseUUIDWrapper.from_string` called with `UUID` (expected `str`).
  - `AlbumResponseDto` may not include `assets` in some DTO versions causing AttributeError at runtime.

Full reproduction steps
1. Checkout branch: `git fetch && git checkout fix/immich-client-dto-compat`
2. Create and activate venv per repository instructions:

```bash
source .venv/bin/activate
```

3. Run the CI mypy check used by Jenkins:

```bash
bash scripts/devtools/quality_gate_py/venv_launcher.sh --mode CHECK --only-check=check_mypy
# or
.venv/bin/python -m mypy immich_autotag
```

Attached logs & evidence
- See `mypy_findings.md` and `backtrace.md` in the same folder. The backtrace shows runtime AttributeError: 'AlbumResponseDto' object has no attribute 'assets'.

What we tried (minimal, non-invasive changes)
- Convert values passed to `BaseUUIDWrapper.from_string` using `str(uid)` when the value might be a `UUID`.
- Use `getattr(dto, "assets", UNSET|None)` before iterating `assets` to avoid attribute errors and make runtime checks explicit.

Requested investigation
1. Confirm whether `immich-client` or Immich server releases changed DTO types/fields recently (focus: `AlbumResponseDto.assets`, user `id` types). Provide exact versions/releases and diffs if found.
2. Determine whether the correct long-term fix is to:
   - adapt wrappers to be robust across DTO versions (recommended), or
   - pin `immich-client` to a specific version and enforce API contract, or
   - update code generation to include missing fields in stubs.
3. Produce minimal, tested patches (diffs) and unit tests that cover both partial (search) and full (detail) DTOs.

Suggested labels
- bug, ci, mypy, needs-investigation, high-priority

Suggested assignees
- `@maintainers`, `@owners` of albums/users modules, and the CI/mypy triage owner.

Checklist (for the issue)
- [ ] Confirm `immich-client` version in CI and local environments
- [ ] Produce exact diffs showing DTO changes (if any)
- [ ] Implement robust wrapper/adapters or update stubs
- [ ] Add unit tests covering partial vs full DTOs
- [ ] Run `check_mypy` and verify CI passes
- [ ] Merge PR and monitor production runs

Notes for LLM collaborators
- The folder contains an LLM-oriented report (`analysis_llm_report.md`) which includes mypy output and runtime backtraces. If you are a model analyzing this, please: (A) look for changes in `immich-client` releases; (B) propose minimal patches that keep runtime safety and typing correctness; (C) generate unit tests simulating DTO variations.


Evidence: mypy findings
```
[CHECK] Running check_mypy …
[RUN] mypy API on immich_autotag
[FAIL] check_mypy failed: 5 findings found

  [ERROR 1] immich_autotag/albums/album/album_user_wrapper.py:43: Argument 1 to "from_string" of "BaseUUIDWrapper" has incompatible type "UUID"; expected "str" [arg-type]
  [ERROR 2] immich_autotag/albums/album/album_dto_state.py:195: "AlbumResponseDto" has no attribute "assets" [attr-defined]
  [ERROR 3] immich_autotag/albums/album/album_dto_state.py:236: "AlbumResponseDto" has no attribute "assets" [attr-defined]
  [ERROR 4] immich_autotag/users/user_response_wrapper.py:64: Argument 1 to "from_string" of "BaseUUIDWrapper" has incompatible type "UUID"; expected "str" [arg-type]
  [ERROR 5] immich_autotag/users/user_response_wrapper.py:72: Incompatible return value type (got "str | UUID", expected "str") [return-value]
```

Evidence: backtrace(s)
```
[PROGRESS] [PROGRESS] [ALBUM-MAP-BUILD] Starting asset-to-albums map construction...
[WARNING] [ERROR] Fatal (Programming error: AttributeError) - Skipping asset 35af67c1-bb78-4d12-b868-385da1757fc2: 'AlbumResponseDto' object has no attribute 'assets'
Traceback:
Traceback (most recent call last):
  File "/home/jenkinsagentub17forub20/txemi/jenkinsagentroot/workspace/h-autotag_ci_skip-mypy-temporary/immich_autotag/assets/process/process_assets_sequential.py", line 63, in process_assets_sequential
    result: AssetProcessReport = process_single_asset(asset_wrapper)
                                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/jenkinsagentub17forub20/txemi/jenkinsagentroot/workspace/h-autotag_ci_skip-mypy-temporary/immich_autotag/assets/process/process_single_asset.py", line 180, in process_single_asset
    result_01_tag_conversion = _apply_tag_conversions(asset_wrapper)
                               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/jenkinsagentub17forub20/txemi/jenkinsagentroot/workspace/h-autotag_ci_skip-mypy-temporary/immich_autotag/assets/process/process_single_asset.py", line 50, in _apply_tag_conversions
    return asset_wrapper.apply_tag_conversions(tag_conversions=tag_conversions)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/jenkinsagentub17forub20/txemi/jenkinsagentroot/workspace/h-autotag_ci_skip-mypy-temporary/immich_autotag/assets/asset_response_wrapper.py", line 732, in apply_tag_conversions
    result: ModificationEntriesList | None = conv.apply_to_asset(self)
                                             ^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/jenkinsagentub17forub20/txemi/jenkinsagentroot/workspace/h-autotag_ci_skip-mypy-temporary/immich_autotag/conversions/conversion_wrapper.py", line 61, in apply_to_asset
    match_result = self.get_source_wrapper().matches_asset(asset_wrapper)
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/jenkinsagentub17forub20/txemi/jenkinsagentroot/workspace/h-autotag_ci_skip-mypy-temporary/immich_autotag/classification/classification_rule_wrapper.py", line 87, in matches_asset
    album_names = set(asset_wrapper.get_album_names())
                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/jenkinsagentub17forub20/txemi/jenkinsagentroot/workspace/h-autotag_ci_skip-mypy-temporary/immich_autotag/assets/asset_response_wrapper.py", line 415, in get_album_names
    return self.get_context().get_albums_collection().album_names_for_asset(self)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/jenkinsagentub17forub20/txemi/jenkinsagentroot/workspace/h-autotag_ci_skip-mypy-temporary/immich_autotag/albums/albums/album_collection_wrapper.py", line 583, in album_names_for_asset
    return [w.get_album_name() for w in self.albums_for_asset(asset)]
                                        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/jenkinsagentub17forub20/txemi/jenkinsagentroot/workspace/h-autotag_ci_skip-mypy-temporary/immich_autotag/albums/albums/album_collection_wrapper.py", line 571, in albums_for_asset
    asset_to_albums_map: AssetToAlbumsMap = self.get_asset_to_albums_map()
                                            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/jenkinsagentub17forub20/txemi/jenkinsagentroot/workspace/h-autotag_ci_skip-mypy-temporary/immich_autotag/albums/albums/album_collection_wrapper.py", line 562, in get_asset_to_albums_map
    self._batch_asset_to_albums_map = asset_map_manager.get_map()
                                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/jenkinsagentub17forub20/txemi/jenkinsagentroot/workspace/h-autotag_ci_skip-mypy-temporary/immich_autotag/albums/albums/asset_map_manager/manager.py", line 159, in get_map
    self._load_map()
  File "/home/jenkinsagentub17forub20/txemi/jenkinsagentroot/workspace/h-autotag_ci_skip-mypy-temporary/immich_autotag/albums/albums/asset_map_manager/manager.py", line 146, in _load_map
    self._build_map()
  File "/home/jenkinsagentub17forub20/txemi/jenkinsagentroot/workspace/h-autotag_ci_skip-mypy-temporary/immich_autotag/albums/albums/asset_map_manager/manager.py", line 103, in _build_map
    f"{len(album_wrapper.get_asset_uuids())} assets.",
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/jenkinsagentub17forub20/txemi/jenkinsagentroot/workspace/h-autotag_ci_skip-mypy-temporary/immich_autotag/albums/album/album_response_wrapper.py", line 184, in get_asset_uuids
    return self._cache_entry.get_asset_uuids()
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/jenkinsagentub17forub20/txemi/jenkinsagentroot/workspace/h-autotag_ci_skip-mypy-temporary/immich_autotag/albums/album/album_cache_entry.py", line 207, in get_asset_uuids
    return self._ensure_full_loaded()._dto.get_asset_uuids()
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/jenkinsagentub17forub20/txemi/jenkinsagentroot/workspace/h-autotag_ci_skip-mypy-temporary/immich_autotag/albums/album/album_dto_state.py", line 236, in get_asset_uuids
    return set(AssetUUID.from_uuid(UUID(a.id)) for a in self._dto.assets)
                                                        ^^^^^^^^^^^^^^^^
AttributeError: 'AlbumResponseDto' object has no attribute 'assets'

[PROGRESS] [PROGRESS] [ALBUM-MAP-BUILD] Starting asset-to-albums map construction...
[WARNING] [ERROR] Fatal (Programming error: AttributeError) - Skipping asset 688582e5-3c0c-4c5c-a154-e999daf2f210: 'AlbumResponseDto' object has no attribute 'assets'
Traceback:
Traceback (most recent call last):
  File "/home/jenkinsagentub17forub20/txemi/jenkinsagentroot/workspace/h-autotag_ci_skip-mypy-temporary/immich_autotag/assets/process/process_assets_sequential.py", line 63, in process_assets_sequential
    result: AssetProcessReport = process_single_asset(asset_wrapper)
                                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/jenkinsagentub17forub20/txemi/jenkinsagentroot/workspace/h-autotag_ci_skip-mypy-temporary/immich_autotag/assets/process/process_single_asset.py", line 180, in process_single_asset
    result_01_tag_conversion = _apply_tag_conversions(asset_wrapper)
                               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/jenkinsagentub17forub20/txemi/jenkinsagentroot/workspace/h-autotag_ci_skip-mypy-temporary/immich_autotag/assets/process/process_single_asset.py", line 50, in _apply_tag_conversions
    return asset_wrapper.apply_tag_conversions(tag_conversions=tag_conversions)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/jenkinsagentub17forub20/txemi/jenkinsagentroot/workspace/h-autotag_ci_skip-mypy-temporary/immich_autotag/assets/asset_response_wrapper.py", line 732, in apply_tag_conversions
    result: ModificationEntriesList | None = conv.apply_to_asset(self)
                                             ^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/jenkinsagentub17forub20/txemi/jenkinsagentroot/workspace/h-autotag_ci_skip-mypy-temporary/immich_autotag/conversions/conversion_wrapper.py", line 61, in apply_to_asset
    match_result = self.get_source_wrapper().matches_asset(asset_wrapper)
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/jenkinsagentub17forub20/txemi/jenkinsagentroot/workspace/h-autotag_ci_skip-mypy-temporary/immich_autotag/classification/classification_rule_wrapper.py", line 87, in matches_asset
    album_names = set(asset_wrapper.get_album_names())
                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/jenkinsagentub17forub20/txemi/jenkinsagentroot/workspace/h-autotag_ci_skip-mypy-temporary/immich_autotag/assets/asset_response_wrapper.py", line 415, in get_album_names
    return self.get_context().get_albums_collection().album_names_for_asset(self)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/jenkinsagentub17forub20/txemi/jenkinsagentroot/workspace/h-autotag_ci_skip-mypy-temporary/immich_autotag/albums/albums/album_collection_wrapper.py", line 583, in album_names_for_asset
    return [w.get_album_name() for w in self.albums_for_asset(asset)]
                                        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/jenkinsagentub17forub20/txemi/jenkinsagentroot/workspace/h-autotag_ci_skip-mypy-temporary/immich_autotag/albums/albums/album_collection_wrapper.py", line 571, in albums_for_asset
    asset_to_albums_map: AssetToAlbumsMap = self.get_asset_to_albums_map()
                                            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/jenkinsagentub17forub20/txemi/jenkinsagentroot/workspace/h-autotag_ci_skip-mypy-temporary/immich_autotag/albums/albums/album_collection_wrapper.py", line 562, in get_asset_to_albums_map
    self._batch_asset_to_albums_map = asset_map_manager.get_map()
                                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/jenkinsagentub17forub20/txemi/jenkinsagentroot/workspace/h-autotag_ci_skip-mypy-temporary/immich_autotag/albums/albums/asset_map_manager/manager.py", line 159, in get_map
    self._load_map()
  File "/home/jenkinsagentub17forub20/txemi/jenkinsagentroot/workspace/h-autotag_ci_skip-mypy-temporary/immich_autotag/albums/albums/asset_map_manager/manager.py", line 146, in _load_map
    self._build_map()
  File "/home/jenkinsagentub17forub20/txemi/jenkinsagentroot/workspace/h-autotag_ci_skip-mypy-temporary/immich_autotag/albums/albums/asset_map_manager/manager.py", line 103, in _build_map
    f"{len(album_wrapper.get_asset_uuids())} assets.",
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/jenkinsagentub17forub20/txemi/jenkinsagentroot/workspace/h-autotag_ci_skip-mypy-temporary/immich_autotag/albums/album/album_response_wrapper.py", line 184, in get_asset_uuids
    return self._cache_entry.get_asset_uuids()
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/jenkinsagentub17forub20/txemi/jenkinsagentroot/workspace/h-autotag_ci_skip-mypy-temporary/immich_autotag/albums/album/album_cache_entry.py", line 207, in get_asset_uuids
    return self._ensure_full_loaded()._dto.get_asset_uuids()
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/jenkinsagentub17forub20/txemi/jenkinsagentroot/workspace/h-autotag_ci_skip-mypy-temporary/immich_autotag/albums/album/album_dto_state.py", line 236, in get_asset_uuids
    return set(AssetUUID.from_uuid(UUID(a.id)) for a in self._dto.assets)
                                                        ^^^^^^^^^^^^^^^^
AttributeError: 'AlbumResponseDto' object has no attribute 'assets'
```
