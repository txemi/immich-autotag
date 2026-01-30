import datetime
import enum
from typing import TYPE_CHECKING
from uuid import UUID

import attrs
from immich_client.models.album_response_dto import AlbumResponseDto

from immich_autotag.assets.asset_uuid import AssetUUID
from immich_autotag.config.cache_config import DEFAULT_CACHE_MAX_AGE_SECONDS
from immich_autotag.types.uuid_wrappers import AlbumUUID

if TYPE_CHECKING:
    from immich_autotag.assets.asset_uuid import AssetUUID

if TYPE_CHECKING:
    from .album_user_list import AlbumUserList


class AlbumLoadSource(enum.Enum):
    """
     Enum to indicate the API call source for an AlbumResponseDto.
    SEARCH: Loaded from album list/search API (partial/summary info).
    DETAIL: Loaded from album detail API (full info).
    """

    SEARCH = "search"
    DETAIL = "detail"


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
        validator=attrs.validators.instance_of(AlbumResponseDto)
    )
    _load_source: AlbumLoadSource = attrs.field(
        validator=attrs.validators.instance_of(AlbumLoadSource)
    )
    _loaded_at: datetime.datetime = attrs.field(
        factory=datetime.datetime.now,
        validator=attrs.validators.instance_of(datetime.datetime),
    )

    _max_age_seconds: int = DEFAULT_CACHE_MAX_AGE_SECONDS

    def __attrs_post_init__(self):
        if self._dto is None:
            raise ValueError("_dto (AlbumResponseDto) cannot be None")

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

        users = [AlbumUserWrapper(user=u) for u in self._dto.album_users]
        return AlbumUserList(users)

    def get_owner_uuid(self) -> "UserUUID":
        from immich_autotag.types.uuid_wrappers import UserUUID
        return UserUUID.from_uuid(UUID(self._dto.owner_id))

    @staticmethod
    def create(
        *, dto: AlbumResponseDto, load_source: AlbumLoadSource
    ) -> "AlbumDtoState":
        """
        Creates a new instance of AlbumDtoState safely to avoid issues with attrs and enums.
        Arguments must be passed by name (not positional).
        """
        return AlbumDtoState(dto=dto, load_source=load_source)

    def is_full(self) -> bool:
        if self._load_source == AlbumLoadSource.DETAIL:
            return True
        elif self._load_source == AlbumLoadSource.SEARCH:
            return False
        else:
            raise RuntimeError(f"Unknown AlbumLoadSource: {self._state.load_source!r}")

    def is_empty(self) -> bool:
        if self._load_source == AlbumLoadSource.SEARCH:
            raise RuntimeError(
                "Cannot determine if album is empty from SEARCH load source."
            )
        return len(self._dto.assets) == 0

    def get_asset_uuids(self) -> set[AssetUUID]:
        """
        Returns the set of asset UUIDs in the album.
        Only allowed in DETAIL/full mode.
        """
        if self._load_source != AlbumLoadSource.DETAIL:
            raise RuntimeError("Cannot get asset UUIDs from SEARCH/partial album DTO.")
        from immich_autotag.assets.asset_uuid import AssetUUID

        return set(AssetUUID.from_uuid(UUID(a.id)) for a in self._dto.assets)

    def _is_stale(self) -> bool:
        import time

        return (time.time() - self.get_loaded_at().timestamp()) > self._max_age_seconds

    def get_assets(self):
        raise NotImplementedError("implement")
