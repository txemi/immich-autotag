from immich_autotag.api.immich_proxy.assets import AssetResponseDto
from immich_autotag.types.uuid_wrappers import AssetUUID
from immich_autotag.utils.url_helpers import get_immich_photo_url


def get_asset_dto_url(dto: AssetResponseDto) -> str:
    """
    Returns the Immich web URL for the given AssetResponseDto.
    Defensive: returns '<invalid url>' if dto or id is invalid.
    """
    try:
        uid = dto.id
        if not uid:
            return "<invalid url>"
        asset_uuid = AssetUUID(str(uid))
        return get_immich_photo_url(asset_uuid).geturl()
    except Exception:
        return "<invalid url>"


def repr_dto_filename_and_id(x: AssetResponseDto | None) -> str:
    if x is None:
        return "None"
    try:
        file_name = x.original_file_name  # type: ignore[attr-defined]
        uid = x.id  # type: ignore[attr-defined]
        asset_url = get_asset_dto_url(x)
    except AttributeError:
        return "AssetResponseDto(<invalid object>)"
    return f"AssetResponseDto(file_name='{file_name}', id='{uid}', url='{asset_url}')"
