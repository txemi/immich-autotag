"""
Object-oriented extractor for UUIDs in Immich links.

Initialize with a URL and obtain album and asset UUIDs via methods.
Designed for future extensibility and private logic encapsulation.
"""

import re
from uuid import UUID

import attrs

from immich_autotag.types.uuid_wrappers import AlbumUUID, AssetUUID

from .immich_url_types import ImmichUrlUuids


@attrs.define(auto_attribs=True, slots=True)
class ImmichUrlUuidExtractor:
    """
    Extracts and classifies UUIDs from an Immich URL.
    Initialize with a URL (private). Methods to get album and asset UUIDs.
    Parsing is lazy and cached: only performed when needed, and result is stored.
    """

    _url: str
    _album_uuid: AlbumUUID | None = attrs.field(init=False, default=None, repr=False)
    _asset_uuid: AssetUUID | None = attrs.field(init=False, default=None, repr=False)
    _parsed: bool = attrs.field(init=False, default=False, repr=False)

    def _parse_if_needed(self) -> None:
        if not self._parsed:
            album_uuid = None
            asset_uuid = None
            # .../albums/{album_uuid}/photos/{asset_uuid}
            m = re.search(
                r"/albums/([a-fA-F0-9\-]{36})/photos/([a-fA-F0-9\-]{36})", self._url
            )
            if m:
                album_uuid = UUID(m.group(1))
                asset_uuid = UUID(m.group(2))
            else:
                m = re.search(r"/albums/([a-fA-F0-9\-]{36})", self._url)
                if m:
                    album_uuid = UUID(m.group(1))
                m2 = re.search(r"/photos/([a-fA-F0-9\-]{36})", self._url)
                if m2:
                    asset_uuid = UUID(m2.group(1))
            self._album_uuid = album_uuid
            self._asset_uuid = asset_uuid
            self._parsed = True

    def get_album_uuid(self) -> AlbumUUID | None:
        self._parse_if_needed()
        return self._album_uuid

    def get_asset_uuid(self) -> AssetUUID | None:
        self._parse_if_needed()
        return self._asset_uuid

    def get_all(self) -> ImmichUrlUuids:
        self._parse_if_needed()
        return ImmichUrlUuids(album_uuid=self._album_uuid, asset_uuid=self._asset_uuid)

    @staticmethod
    def extract_asset_uuids_from_links(links: list[str]) -> list[AssetUUID | None]:
        """
        Given a sequence of links (strings), returns a list with the asset UUID found in each link.
        If a link does not contain an asset UUID, None is placed in that position.
        """
        return [ImmichUrlUuidExtractor(link).get_asset_uuid() for link in links]
