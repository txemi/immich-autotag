import datetime
import enum
from typing import TYPE_CHECKING

import attrs
from immich_client.models.album_response_dto import AlbumResponseDto
from immich_client.types import Unset

from immich_autotag.config.cache_config import DEFAULT_CACHE_MAX_AGE_SECONDS
from immich_autotag.types.uuid_wrappers import AlbumUUID, AssetUUID, UserUUID

if TYPE_CHECKING:
    from .album_user_list import AlbumUserList

from immich_autotag.albums.album.album_url_helpers import album_url_from_dto

# Value of AlbumUserRole.OWNER (Immich >= v3). Compared as text because the v2
# client has no OWNER member.
_OWNER_ROLE = "owner"


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

    # Album membership. Since Immich v3 the album DTO no longer embeds its
    # assets, so the asset UUIDs are fetched apart (POST /search/metadata with
    # albumIds) and kept here. None means "not loaded": the state is partial.
    # A DTO update (rename, re-list) does not change membership, so it keeps
    # the set; only a fresh DETAIL load replaces it.
    _asset_uuids: "set[AssetUUID] | None" = attrs.field(
        default=None, kw_only=True, eq=False, repr=False
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
        # The constructor converts both UUID (client >= v3) and str (v2).
        return AlbumUUID(self._dto.id)

    def get_album_name(self) -> str:
        """Returns the album name (without exposing the full DTO)."""
        return self._dto.album_name

    def get_load_source(self) -> AlbumLoadSource:
        """Returns the API source from which the album was obtained."""
        return self._load_source

    def get_loaded_at(self) -> datetime.datetime:
        """Returns the timestamp when the album was obtained."""
        return self._loaded_at

    def update(
        self,
        *,
        dto: AlbumResponseDto,
        load_source: AlbumLoadSource,
        asset_uuids: "set[AssetUUID] | None" = None,
    ) -> None:
        """
        Updates the state with a new DTO, source, and current timestamp.
        Ensures loaded_at never goes backwards in time.
        The album membership is replaced only when asset_uuids is given.
        """
        now = datetime.datetime.now()
        if self._loaded_at and now < self._loaded_at:
            raise RuntimeError(
                "New loaded_at timestamp is earlier than previous loaded_at."
            )
        self._dto = dto
        self._load_source = load_source
        self._loaded_at = now
        if asset_uuids is not None:
            self._asset_uuids = asset_uuids

    def get_album_users(self) -> "AlbumUserList":
        """
        Returns the users the album is shared with, without the owner.

        Since Immich v3 the owner is listed in album_users with role `owner`;
        before, it was only in owner/ownerId. The owner is left out so that
        callers (permission sync) keep seeing only shared members.
        """
        from .album_user_list import AlbumUserList
        from .album_user_wrapper import AlbumUserWrapper

        users = [
            AlbumUserWrapper(u)
            for u in self._dto.album_users
            if str(u.role) != _OWNER_ROLE
        ]
        return AlbumUserList(users)

    def get_owner_uuid(self) -> UserUUID:
        for album_user in self._dto.album_users:
            if str(album_user.role) == _OWNER_ROLE:
                return UserUUID(album_user.user.id)
        # Immich v2: the owner is not in album_users but in ownerId, a field the
        # v3 client does not declare; to_dict() reads it with either client.
        owner_id = self._dto.to_dict().get("ownerId")
        if not isinstance(owner_id, str):
            raise RuntimeError(f"Album {self._dto.id} has no owner in its DTO.")
        return UserUUID(owner_id)

    @staticmethod
    def create(
        *,
        dto: AlbumResponseDto,
        load_source: AlbumLoadSource,
        asset_uuids: "set[AssetUUID] | None" = None,
    ) -> "AlbumDtoState":
        """
        Creates a new instance of AlbumDtoState safely to avoid issues with attrs and enums.
        Arguments must be passed positionally to match attrs usage.
        """
        return AlbumDtoState(dto, load_source, asset_uuids=asset_uuids)

    def is_full(self) -> bool:
        """
        Whether the album membership is loaded. A DETAIL DTO alone is no
        longer enough: since Immich v3 the assets are fetched apart.
        """
        if self._load_source == AlbumLoadSource.SEARCH:
            return False
        if self._load_source in (AlbumLoadSource.DETAIL, AlbumLoadSource.UPDATE):
            return self._asset_uuids is not None
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
        Only allowed in full mode (membership loaded).
        """
        if self._asset_uuids is None:
            raise RuntimeError(
                "Cannot get asset UUIDs from a partial album state "
                f"(load source {self._load_source.value}, membership not loaded)."
            )
        return self._asset_uuids

    def is_stale(self) -> bool:
        import time

        return (time.time() - self.get_loaded_at().timestamp()) > self._max_age_seconds

    def get_album_uuid(self) -> AlbumUUID:
        return AlbumUUID(self._dto.id)

    def get_immich_album_url(self):
        return album_url_from_dto(self._dto)

    @staticmethod
    def from_album_info(
        album_info: AlbumResponseDto, load_source: AlbumLoadSource
    ) -> "AlbumDtoState":
        return AlbumDtoState.create(dto=album_info, load_source=load_source)
