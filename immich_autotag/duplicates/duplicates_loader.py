from typing import Optional

import attrs
from immich_client import Client
from immich_client.api.duplicates import get_asset_duplicates

from immich_autotag.duplicates.duplicate_collection_wrapper import \
    DuplicateCollectionWrapper


@attrs.define(auto_attribs=True, slots=True)
class DuplicatesLoader:
    client: Client
    duplicates: Optional[DuplicateCollectionWrapper] = None

    def load(self):
        # Usa la función de alto nivel del cliente para obtener duplicados
        duplicates_dto_list = get_asset_duplicates.sync(client=self.client)
        self.duplicates = DuplicateCollectionWrapper.from_api_response(
            duplicates_dto_list
        )
        return self.duplicates
