import attrs
from immich_autotag.config.models import Destination

@attrs.define(auto_attribs=True, slots=True, frozen=True, eq=True)
class DestinationWrapper:
    destination: Destination = attrs.field()

    # Aquí puedes añadir métodos avanzados para Destination
    def get_tag_names(self) -> list[str]:
        return self.destination.tag_names or []

    def get_album_names(self) -> list[str]:
        return self.destination.album_names or []
