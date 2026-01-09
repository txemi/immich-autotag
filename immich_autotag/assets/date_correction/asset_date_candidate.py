from datetime import datetime
from typing import Optional

import attrs

from immich_autotag.assets.asset_response_wrapper import AssetResponseWrapper

from .date_source_kind import DateSourceKind


@attrs.define(auto_attribs=True, slots=True)
class AssetDateCandidate:
    """
    Represents a candidate date offered by an asset (can be the main asset or a duplicate).
    Each instance corresponds to a possible date source for that asset, such as the Immich date, the date extracted from the filename, from the path, EXIF, etc.

    - source_kind: Indicates the type of date source (see DateSourceKind).
    - date: The specific date offered by that source.
    - file_path: Path or filename relevant to the source (can be None).
    - asset_wrapper: Reference to the asset offering this date (can be the main or a duplicate).

    Example: An asset can have several candidate dates (Immich, filename, EXIF, etc.), each represented by an instance of this class.
    """

    asset_wrapper: AssetResponseWrapper = attrs.field(
        validator=attrs.validators.instance_of(AssetResponseWrapper)
    )
    source_kind: DateSourceKind = attrs.field(
        validator=attrs.validators.instance_of(DateSourceKind)
    )
    _date: datetime = attrs.field(validator=attrs.validators.instance_of(datetime))
    file_path: Optional[str] = attrs.field(
        default=None,
        validator=attrs.validators.optional(attrs.validators.instance_of(str)),
    )

    from typeguard import typechecked

    @typechecked
    def __str__(self) -> str:
        return f"AssetDateCandidate(source_kind={self.source_kind}, date={self.get_aware_date()}, file_path={self.file_path}, asset_id={getattr(self.asset_wrapper, 'id', None)})"

    @typechecked
    def get_aware_date(self, user_tz: Optional[str] = None) -> datetime:
        """
        Returns the date as an aware datetime (with timezone).
        If the date is naive, uses the user timezone (user_tz) or the one defined in configuration (DATE_EXTRACTION_TIMEZONE).
        """
        dt = self._date
        if dt.tzinfo is not None:
            return dt

        if user_tz:
            tz = user_tz
        else:
            from immich_autotag.config.manager import ConfigManager

            manager = ConfigManager.get_instance()
            if not manager or not manager.config or not manager.config.features:
                raise RuntimeError("ConfigManager or features config not initialized")
            tz = manager.config.features.date_correction.extraction_timezone
        from zoneinfo import ZoneInfo

        return dt.replace(tzinfo=ZoneInfo(tz))

    @typechecked
    def __lt__(self, other: object) -> bool:
        if not isinstance(other, AssetDateCandidate):
            return NotImplemented
        return self.get_aware_date() < other.get_aware_date()

    @typechecked
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, AssetDateCandidate):
            return NotImplemented
        return self.get_aware_date() == other.get_aware_date()

    @typechecked
    def format_info(self) -> str:
        aw = self.asset_wrapper
        link = (
            aw.get_immich_photo_url().geturl()
            if hasattr(aw, "get_immich_photo_url")
            else "(no link)"
        )
        return f"[{self.source_kind.name}] date={self.get_aware_date()} | file_path={self.file_path} | asset_id={aw.id} | link={link}"
