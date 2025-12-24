import attrs
from typeguard import typechecked
from immich_client.models.album_response_dto import AlbumResponseDto
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from immich_client.models.asset_response_dto import AssetResponseDto
    from .asset_response_wrapper import AssetResponseWrapper
    from .tag_collection_wrapper import TagCollectionWrapper
    from .main import ImmichContext

@attrs.define(auto_attribs=True, slots=True, frozen=True)
class AlbumResponseWrapper:
    album: AlbumResponseDto = attrs.field(
        validator=attrs.validators.instance_of(AlbumResponseDto)
    )

    @typechecked
    def has_asset(self, asset: 'AssetResponseDto') -> bool:
        if self.album.assets:
            return any(a.id == asset.id for a in self.album.assets)
        return False

    @typechecked
    def wrapped_assets(self, context: 'ImmichContext') -> list['AssetResponseWrapper']:
        return (
            [AssetResponseWrapper(asset=a, context=context) for a in self.album.assets]
            if self.album.assets
            else []
        )

@attrs.define(auto_attribs=True, slots=True, frozen=True)
class AlbumCollectionWrapper:
    albums: list[AlbumResponseWrapper] = attrs.field(
        validator=attrs.validators.instance_of(list)
    )

    @typechecked
    def albums_for_asset(self, asset: 'AssetResponseDto') -> list[str]:
        album_names = []
        for album_wrapper in self.albums:
            if album_wrapper.has_asset(asset):
                album_names.append(album_wrapper.album.album_name)
        return album_names
