import attrs
from datetime import datetime
from typing import Optional

from immich_autotag.assets.date_correction.asset_date_candidate import AssetDateCandidate



@attrs.define(auto_attribs=True, slots=True)
class AssetDateSources:
    asset_id: str
    immich_date: Optional[AssetDateCandidate]
    whatsapp_filename_date: Optional[AssetDateCandidate]
    whatsapp_path_date: Optional[AssetDateCandidate]

    def all_candidates(self) -> list[AssetDateCandidate]:
        """Return all non-None AssetDateCandidate objects as a list."""
        return [
            d for d in [
                self.immich_date,
                self.whatsapp_filename_date,
                self.whatsapp_path_date,
            ] if d is not None
        ]

    def oldest_candidate(self) -> Optional[AssetDateCandidate]:
        """Return the AssetDateCandidate with the oldest date, or None if none found."""
        candidates = self.all_candidates()
        return min(candidates, key=lambda c: c.date) if candidates else None

    def __attrs_post_init__(self):
        # Optionally, add integrity checks here
        pass

    def add_candidates_to(self, candidate_list: list) -> None:
        """
        Add all non-None AssetDateCandidate objects from this asset to the provided list.
        """
        for candidate in self.all_candidates():
            candidate_list.append(candidate)
