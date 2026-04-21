
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