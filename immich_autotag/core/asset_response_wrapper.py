import attrs
from typeguard import typechecked
from typing import TYPE_CHECKING
from immich_client.models.asset_response_dto import AssetResponseDto

if TYPE_CHECKING:
    from .ejemplo_immich_client import ImmichContext
    from .main import TagModificationReport

@attrs.define(auto_attribs=True, slots=True, frozen=True)
class AssetResponseWrapper:
    asset: AssetResponseDto = attrs.field(
        validator=attrs.validators.instance_of(AssetResponseDto)
    )
    context: "ImmichContext" = attrs.field(
        validator=attrs.validators.instance_of(object)
    )

    def __attrs_post_init__(self):
        if not isinstance(self.context, ImmichContext):
            raise TypeError(f"context debe ser ImmichContext, no {type(self.context)}")

    @typechecked
    def has_tag(self, tag_name: str) -> bool:
        return (
            any(tag.name.lower() == tag_name.lower() for tag in self.asset.tags)
            if self.asset.tags
            else False
        )

    # ... (rest of methods should be migrated from main.py)
