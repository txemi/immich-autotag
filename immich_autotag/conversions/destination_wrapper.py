
import attrs
from typeguard import typechecked

from immich_autotag.config.models import Destination


@attrs.define(auto_attribs=True, slots=True, frozen=True, eq=True)
class DestinationWrapper:
    destination: Destination = attrs.field()

    # Aquí puedes añadir métodos avanzados para Destination
    def get_tag_names(self) -> list[str]:
        return self.destination.tag_names or []

    def get_album_names(self) -> list[str]:
        return self.destination.album_names or []

    @typechecked
    def apply_action(self, asset_wrapper: "AssetResponseWrapper") -> list[str]:
        """
        Aplica la acción de destino sobre el asset_wrapper.
        Añade todas las etiquetas destino y añade el asset a todos los álbumes destino si no están ya.
        """
        changes = []
        # Añadir etiquetas destino
        for tag in self.get_tag_names():
            if not asset_wrapper.has_tag(tag):
                try:
                    asset_wrapper.add_tag_by_name(tag)
                    changes.append(f"Added tag '{tag}'")
                except Exception as e:
                    changes.append(f"Failed to add tag '{tag}': {e}")
        # Añadir a álbumes destino
        for album in self.get_album_names():
            if album not in asset_wrapper.get_album_names():
                try:
                    asset_wrapper.context.albums_collection.add_asset_to_album(
                        asset_wrapper, album
                    )
                    changes.append(f"Added asset to album '{album}'")
                except Exception as e:
                    changes.append(f"Failed to add asset to album '{album}': {e}")
        return changes

    def __attrs_post_init__(self):
        if not (self.get_tag_names() or self.get_album_names()):
            raise ValueError(
                "DestinationWrapper: destination debe tener al menos un tag o un álbum de destino."
            )
