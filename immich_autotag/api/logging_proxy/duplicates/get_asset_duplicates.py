"""
Logging proxy for duplicate asset operations.
Incluye loader de duplicados de alto nivel y wrapper de proxy.
"""

from typing import Optional

import attrs
from immich_client.client import AuthenticatedClient

from immich_autotag.api.immich_proxy.duplicates import proxy_get_asset_duplicates
from immich_autotag.duplicates.duplicate_collection_wrapper import (
    DuplicateCollectionWrapper,
)


@attrs.define(auto_attribs=True, slots=True)
class DuplicatesLoader:
    client: AuthenticatedClient
    duplicates: Optional[DuplicateCollectionWrapper] = None

    def load(self):
        duplicates_dto_list = proxy_get_asset_duplicates(client=self.client)
        self.duplicates = DuplicateCollectionWrapper.from_api_response(
            duplicates_dto_list
        )
        return self.duplicates


__all__ = ["proxy_get_asset_duplicates", "DuplicatesLoader"]
