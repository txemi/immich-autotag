import attrs
from datetime import datetime
from typing import Optional

@attrs.define(auto_attribs=True, slots=True)
class AssetDateSources:
    asset_id: str
    immich_date: Optional[datetime]
    whatsapp_filename_date: Optional[datetime]
    whatsapp_path_date: Optional[datetime]

    def all_dates(self):
        """Return all non-None dates as a list."""
        return [d for d in [self.immich_date, self.whatsapp_filename_date, self.whatsapp_path_date] if d is not None]

    def oldest_date(self) -> Optional[datetime]:
        """Return the oldest date found, or None if none found."""
        dates = self.all_dates()
        return min(dates) if dates else None

    def __attrs_post_init__(self):
        # Optionally, add integrity checks here
        pass
    def add_candidates_to(self, candidate_list: list) -> None:
        """
        Add all non-None date candidates from this asset to the provided list as (label, date) tuples.
        """
        if self.immich_date:
            candidate_list.append((f"immich_date {self.asset_id}", self.immich_date))
        if self.whatsapp_filename_date:
            candidate_list.append((f"wa_filename_date {self.asset_id}", self.whatsapp_filename_date))
        if self.whatsapp_path_date:
            candidate_list.append((f"wa_path_date {self.asset_id}", self.whatsapp_path_date))
