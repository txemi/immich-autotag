[CHECK] Running check_mypy …
[RUN] mypy API on immich_autotag
[FAIL] check_mypy failed: 5 findings found

  [ERROR 1] immich_autotag/albums/album/album_user_wrapper.py:43: Argument 1 to "from_string" of "BaseUUIDWrapper" has incompatible type "UUID"; expected "str" [arg-type]
  [ERROR 2] immich_autotag/albums/album/album_dto_state.py:195: "AlbumResponseDto" has no attribute "assets" [attr-defined]
  [ERROR 3] immich_autotag/albums/album/album_dto_state.py:236: "AlbumResponseDto" has no attribute "assets" [attr-defined]
  [ERROR 4] immich_autotag/users/user_response_wrapper.py:64: Argument 1 to "from_string" of "BaseUUIDWrapper" has incompatible type "UUID"; expected "str" [arg-type]
  [ERROR 5] immich_autotag/users/user_response_wrapper.py:72: Incompatible return value type (got "str | UUID", expected "str") [return-value]