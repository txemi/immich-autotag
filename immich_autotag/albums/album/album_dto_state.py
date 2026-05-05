import datetime
import enum
from typing import TYPE_CHECKING
from uuid import UUID

import attrs
from immich_client.models.album_response_dto import AlbumResponseDto
from immich_client.types import Unset

from immich_autotag.config.cache_config import DEFAULT_CACHE_MAX_AGE_SECONDS
from immich_autotag.types.uuid_wrappers import AlbumUUID, AssetUUID, UserUUID

if TYPE_CHECKING:
    from .album_user_list import AlbumUserList

from immich_autotag.albums.album.album_url_helpers import album_url_from_dto


class AlbumLoadSource(enum.Enum):
    """
     Enum to indicate the API call source for an AlbumResponseDto.
    SEARCH: Loaded from album list/search API (partial/summary info).
    DETAIL: Loaded from album detail API (full info).
    UPDATE: Used when updating album information.
    """

    SEARCH = "search"
    DETAIL = "detail"
    UPDATE = "update"


@attrs.define(auto_attribs=True, slots=True)
class AlbumDtoState:
    """
    Encapsulates the state of an AlbumResponseDto retrieved from the API.

    This class groups three attributes that are always obtained together when querying an album:
    - The album DTO (private, not exposed directly)
    - The AlbumLoadSource enum indicating the API source
    - The loaded_at timestamp

    The DTO is not exposed directly. Access must be through public methods
    that return only the necessary information.
    """

    _dto: AlbumResponseDto = attrs.field(
        validator=attrs.validators.instance_of(AlbumResponseDto),
        repr=lambda dto: f"AlbumResponseDto(id={dto.id}, url={album_url_from_dto(dto)})",
    )

    _load_source: AlbumLoadSource = attrs.field(
        validator=attrs.validators.instance_of(AlbumLoadSource)
    )
    _loaded_at: datetime.datetime = attrs.field(
        factory=datetime.datetime.now,
        validator=attrs.validators.instance_of(datetime.datetime),
    )

    _max_age_seconds: int = DEFAULT_CACHE_MAX_AGE_SECONDS

    # Lazy cache for the asset UUID set: get_asset_uuids() is called many times
    # per processed asset (e.g. via has_asset_wrapper before each add). Building
    # the set from `self._dto.assets` is O(N) per call, with N up to ~100k for
    # the largest albums; typeguard validation of every UUID dominates CPU.
    # The state is effectively immutable (the DTO does not mutate after load),
    # so caching the set is safe within the lifetime of this state instance.
    _asset_uuids_cache: "set[AssetUUID] | None" = attrs.field(
        default=None, init=False, eq=False, repr=False
    )

    def __attrs_post_init__(self):
        # _dto is always required and validated by attrs; no need to check for None
        pass

    def get_start_date(self) -> datetime.datetime | Unset:
        """
        Returns the album's start date as a datetime object.

        Raises:
            TypeError: If start_date is not a datetime (including None, Unset, or any other type).
                      Fails fast to discover actual API behavior in production.
        """
        value = self._dto.start_date

        if isinstance(value, datetime.datetime):
            return value
        if isinstance(value, Unset):
            return value

        # Fail fast for any non-datetime value (None, Unset, string, etc.)
        raise TypeError(
            f"Album start_date must be datetime.datetime, got {type(value).__name__!r}: {value!r}"
        )

    def get_end_date(self) -> datetime.datetime | Unset:
        """
        Returns the album's end date as a datetime object.

        Raises:
            TypeError: If end_date is not a datetime (including None, Unset, or any other type).
                      Fails fast to discover actual API behavior in production.
        """
        value = self._dto.end_date

        if isinstance(value, datetime.datetime):
            return value
        if isinstance(value, Unset):
            return value
        # Fail fast for any non-datetime value (None, Unset, string, etc.)
        raise TypeError(
            f"Album end_date must be datetime.datetime, got {type(value).__name__!r}: {value!r}"
        )

    def get_dto(self) -> AlbumResponseDto:
        """Returns the underlying AlbumResponseDto (for internal use only)."""
        return self._dto

    def _update_from_dto(
        self, dto: AlbumResponseDto, load_source: "AlbumLoadSource"
    ) -> None:
        self.update(dto=dto, load_source=load_source)

    def _set_album_full(self, value: AlbumResponseDto) -> None:
        self._update_from_dto(value, AlbumLoadSource.DETAIL)

    def merge_from_dto(
        self, dto: AlbumResponseDto, load_source: "AlbumLoadSource"
    ) -> None:
        """
        Unifies DTO update logic. Updates the state with the new DTO and load_source if:
                - The new load_source is DETAIL (always update to full)
                - The current load_source is SEARCH (allow update from SEARCH to SEARCH or
                    DETAIL)
        - Ensures loaded_at is monotonic (never decreases)
        - Updates asset ID cache as UUIDs
        If the current is DETAIL and the new is SEARCH, ignores the update.
        """
        should_update = False
        current_load_source = self._load_source
        if load_source == AlbumLoadSource.DETAIL:
            should_update = True
        elif current_load_source == AlbumLoadSource.SEARCH:
            should_update = True
        if should_update:
            self._update_from_dto(dto, load_source)

    def get_album_id(self) -> AlbumUUID:
        """Returns the album ID as strongly-typed AlbumUUID."""
        return AlbumUUID.from_uuid(UUID(self._dto.id))

    def get_album_name(self) -> str:
        """Returns the album name (without exposing the full DTO)."""
        return self._dto.album_name

    def get_load_source(self) -> AlbumLoadSource:
        """Returns the API source from which the album was obtained."""
        return self._load_source

    def get_loaded_at(self) -> datetime.datetime:
        """Returns the timestamp when the album was obtained."""
        return self._loaded_at

    def update(self, *, dto: AlbumResponseDto, load_source: AlbumLoadSource) -> None:
        """
        Updates the state with a new DTO, source, and current timestamp.
        Ensures loaded_at never goes backwards in time.
        """
        now = datetime.datetime.now()
        if self._loaded_at and now < self._loaded_at:
            raise RuntimeError(
                "New loaded_at timestamp is earlier than previous loaded_at."
            )
        self._dto = dto
        self._load_source = load_source
        self._loaded_at = now

    def get_album_users(self) -> "AlbumUserList":
        from .album_user_list import AlbumUserList
        from .album_user_wrapper import AlbumUserWrapper

        users = [AlbumUserWrapper(u) for u in self._dto.album_users]
        return AlbumUserList(users)

    def get_owner_uuid(self) -> UserUUID:
        return UserUUID.from_string(self._dto.owner_id)

    @staticmethod
    def create(
        *, dto: AlbumResponseDto, load_source: AlbumLoadSource
    ) -> "AlbumDtoState":
        """
        Creates a new instance of AlbumDtoState safely to avoid issues with attrs and enums.
        Arguments must be passed positionally to match attrs usage.
        """
        return AlbumDtoState(dto, load_source)

    def is_full(self) -> bool:
        if self._load_source == AlbumLoadSource.DETAIL:
            return True
        elif self._load_source == AlbumLoadSource.SEARCH:
            return False
        elif self._load_source == AlbumLoadSource.UPDATE:
            from immich_client.types import UNSET, Unset

            if self._dto.assets is UNSET or self._dto.assets is Unset:
                raise RuntimeError("UPDATE load source must have assets field set.")
            return True
        else:
            raise RuntimeError(f"Unknown AlbumLoadSource: {self._load_source!r}")

    def is_empty(self) -> bool:
        """
        Returns whether the album has no assets.

        Uses the asset_count field from the DTO, which is available
        regardless of load source and avoids deserializing the full assets list.
        """
        return self._dto.asset_count == 0

    def has_assets(self) -> bool:
        """
        Returns whether the album has at least one asset.

        Inverse of is_empty(). Uses asset_count for efficiency.
        """
        return self._dto.asset_count > 0

    def get_asset_count(self) -> int:
        """
        Returns the number of assets in the album.

        This is available regardless of load source (SEARCH, DETAIL, UPDATE)
        and is more efficient than accessing the assets list directly.
        """
        return self._dto.asset_count

    def get_asset_uuids(self) -> set[AssetUUID]:
        """
        Returns the set of asset UUIDs in the album.
        Only allowed in DETAIL/full mode.
        """
        if self._load_source != AlbumLoadSource.DETAIL:
            raise RuntimeError("Cannot get asset UUIDs from SEARCH/partial album DTO.")
        if self._asset_uuids_cache is None:
            # AssetUUID is already imported at module scope (line 11).
            # A local `from ... import AssetUUID` here would shadow that module-level
            # binding and make AssetUUID a *local* variable for the whole function;
            # then typeguard's evaluation of the `set[AssetUUID]` return annotation
            # (under conditional_typechecked) raises UnboundLocalError on the cached
            # code path, where the import line is skipped.
            self._asset_uuids_cache = set(
                AssetUUID.from_uuid(UUID(a.id)) for a in self._dto.assets
            )
        return self._asset_uuids_cache

    def is_stale(self) -> bool:
        import time

        return (time.time() - self.get_loaded_at().timestamp()) > self._max_age_seconds

    def get_assets(self):
        """
        Returns the full list of assets in the album.

        WARNING: Only available in DETAIL/full mode. In SEARCH mode, assets
        may be empty even if asset_count > 0. Use get_asset_count() for
        checking the number of assets without deserializing this list.
        """
        return self._dto.assets

    def get_album_uuid(self) -> AlbumUUID:
        return AlbumUUID.from_uuid_string(self._dto.id)

    def get_immich_album_url(self):
        return album_url_from_dto(self._dto)

    @staticmethod
    def from_album_info(
        album_info: AlbumResponseDto, load_source: AlbumLoadSource
    ) -> "AlbumDtoState":
        return AlbumDtoState.create(dto=album_info, load_source=load_source)
