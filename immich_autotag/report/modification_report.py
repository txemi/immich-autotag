"""
Module for auditing and reporting entity modifications (tags, albums, assets, etc.)
"""

from __future__ import annotations

import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional
from urllib.parse import ParseResult

import attrs

from immich_autotag.utils.run_output_dir import get_run_output_dir

if TYPE_CHECKING:
    from immich_autotag.albums.album_response_wrapper import AlbumResponseWrapper
    from immich_autotag.assets.asset_response_wrapper import AssetResponseWrapper
    from immich_autotag.tags.tag_response_wrapper import TagWrapper

from immich_autotag.report.modification_entry import ModificationEntry
from immich_autotag.tags.modification_kind import ModificationKind
from immich_autotag.users.user_response_wrapper import UserResponseWrapper

_instance = None  # Singleton instance
_instance_created = False  # Class-level flag


# Classes that will go here:
# - ModificationEntry
# - SerializableModificationEntry
# - TagModificationReport (possibly renamed)
@attrs.define(auto_attribs=True, slots=True)
class ModificationReport:

    import datetime as dt
    import os

    log_dir: Path = attrs.field(
        default=get_run_output_dir(), validator=attrs.validators.instance_of(Path)
    )
    report_path: Path = attrs.field(
        factory=lambda: get_run_output_dir() / "modification_report.txt",
        validator=attrs.validators.instance_of(Path),
    )
    batch_size: int = attrs.field(
        default=1, validator=attrs.validators.instance_of(int)
    )
    modifications: list[ModificationEntry] = attrs.field(  # type: ignore
        factory=list, init=False
    )
    _since_last_flush: int = attrs.field(
        default=0, init=False, validator=attrs.validators.instance_of(int)
    )
    _cleared_report: bool = attrs.field(
        default=False,
        init=False,
        repr=False,
        validator=attrs.validators.instance_of(bool),
    )

    def __attrs_post_init__(self):
        global _instance, _instance_created
        if _instance_created:
            raise RuntimeError(
                "TagModificationReport instance already exists. Use TagModificationReport.get_instance() instead of creating a new one."
            )
        _instance_created = True
        _instance = self

    @staticmethod
    def get_instance() -> "ModificationReport":
        global _instance
        if _instance is None:
            ModificationReport()
        return _instance  # type: ignore[return-value]

    from typeguard import typechecked

    # todo: tag is being passed as string in several functions, consider using wrapper
    # todo: asset_wrapper is being passed as Any in several functions, type correctly
    @typechecked
    def add_modification(
        self,
        kind: ModificationKind,
        asset_wrapper: Optional["AssetResponseWrapper"] = None,
        tag: Optional["TagWrapper"] = None,
        album: Optional["AlbumResponseWrapper"] = None,
        old_value: Optional[str] = None,
        new_value: Optional[str] = None,
        user: Optional[UserResponseWrapper] = None,
        extra: Optional[dict[str, Any]] = None,
    ) -> None:
        # Local import to avoid circularity
        if album is not None:
            from immich_autotag.albums.album_response_wrapper import (
                AlbumResponseWrapper,
            )

            assert isinstance(album, AlbumResponseWrapper)
        """
        Registers a modification for any entity (tag, album, assignment, etc.).
        """
        if not self._cleared_report:
            try:
                self.report_path.parent.mkdir(parents=True, exist_ok=True)
                with self.report_path.open("w", encoding="utf-8"):
                    pass  # Truncate the file
            except Exception as e:
                print(f"[WARN] Could not clear the tag modification report: {e}")
            self._cleared_report = True

        # If user is None, obtain it using the asset_wrapper context (if it exists)
        user_instance = user
        if user_instance is None:
            user_instance = UserResponseWrapper.from_context(asset_wrapper.context)

        # Calculate progress using StatisticsManager (without try/except)
        from immich_autotag.statistics.statistics_manager import StatisticsManager

        stats_manager = StatisticsManager.get_instance()
        stats = stats_manager.get_stats()
        progress_str = stats_manager.get_progress_description()

        entry = ModificationEntry(
            datetime=datetime.datetime.now(),
            kind=kind,
            asset_wrapper=asset_wrapper,
            tag=tag,
            album=album,
            old_value=old_value,
            new_value=new_value,
            user=user_instance,
            extra=extra,
            progress=progress_str,
        )
        self.modifications.append(entry)
        # Centralized statistics update for tag actions (now encapsulated in StatisticsManager)
        from immich_autotag.statistics.statistics_manager import StatisticsManager

        StatisticsManager.get_instance().increment_tag_action(
            tag=tag, kind=kind, album=album
        )
        self._since_last_flush += 1
        if self._since_last_flush >= self.batch_size:
            self.flush()

    # todo: review old_name and new_name usage, since they are not only used for names, it might be better to use old_value and new_value?
    # Specific methods for each action type
    @typechecked
    def add_tag_modification(
        self,
        kind: ModificationKind,
        asset_wrapper: Optional["AssetResponseWrapper"] = None,
        tag: Optional["TagWrapper"] = None,
        old_value: Optional[str] = None,
        new_value: Optional[str] = None,
        user: Optional[UserResponseWrapper] = None,
    ) -> None:
        assert kind in {
            ModificationKind.ADD_TAG_TO_ASSET,
            ModificationKind.REMOVE_TAG_FROM_ASSET,
            ModificationKind.REMOVE_TAG_GLOBALLY,
        }
        self.add_modification(
            kind=kind,
            asset_wrapper=asset_wrapper,
            tag=tag,
            old_value=old_value,
            new_value=new_value,
            user=user,
        )

    @typechecked
    def add_album_modification(
        self,
        kind: ModificationKind,
        album: "AlbumResponseWrapper",
        old_value: Optional[str] = None,
        new_value: Optional[str] = None,
        user: Optional[UserResponseWrapper] = None,
        extra: Optional[dict[str, Any]] = None,
    ) -> None:
        """
        Registers a modification related to an album (e.g., rename, create).
        """
        assert kind in {
            ModificationKind.CREATE_ALBUM,
            ModificationKind.DELETE_ALBUM,
            ModificationKind.RENAME_ALBUM,
        }
        self.add_modification(
            kind=kind,
            asset_wrapper=None,
            album=album,
            old_value=old_value,
            new_value=new_value,
            user=user,
            extra=extra,
        )

    @typechecked
    def add_assignment_modification(
        self,
        kind: ModificationKind,
        asset_wrapper: Optional["AssetResponseWrapper"] = None,
        album: Optional["AlbumResponseWrapper"] = None,
        user: Optional[UserResponseWrapper] = None,
    ) -> None:
        assert kind in {
            ModificationKind.ASSIGN_ASSET_TO_ALBUM,
            ModificationKind.REMOVE_ASSET_FROM_ALBUM,
        }
        self.add_modification(
            kind=kind,
            asset_wrapper=asset_wrapper,
            album=album,
            user=user,
        )

    @typechecked
    def flush(self) -> None:
        """Flushes the report to file (append)."""
        if not self.modifications or self._since_last_flush == 0:
            return
        import os

        os.makedirs(os.path.dirname(self.report_path), exist_ok=True)
        with open(self.report_path, "a", encoding="utf-8") as f:
            for entry in self.modifications[-self._since_last_flush :]:
                f.write(self._format_modification_entry(entry) + "\n")
        self._since_last_flush = 0

    @typechecked
    def print_summary(self) -> None:
        print("\n[SUMMARY] Modifications:")
        for entry in self.modifications:
            print(self._format_modification_entry(entry))
        print(f"Total modifications: {len(self.modifications)}")

    @typechecked
    def _build_link(
        self,
        kind: ModificationKind,
        asset_wrapper: Any = None,
        album_wrapper: Any = None,
    ) -> Optional["ParseResult"]:
        """
        Build a link for the modification entry based on kind and wrappers.
        """
        from immich_autotag.utils.get_immich_album_url import get_immich_photo_url

        # If it's an asset, use the wrapper method
        if (
            kind
            in {
                ModificationKind.ADD_TAG_TO_ASSET,
                ModificationKind.REMOVE_TAG_FROM_ASSET,
                ModificationKind.REMOVE_TAG_GLOBALLY,
                ModificationKind.ASSIGN_ASSET_TO_ALBUM,
                ModificationKind.REMOVE_ASSET_FROM_ALBUM,
            }
            and asset_wrapper is not None
        ):
            if hasattr(asset_wrapper, "get_immich_photo_url"):
                return asset_wrapper.get_immich_photo_url()
            asset_id = getattr(asset_wrapper, "id_as_uuid", None)
            if asset_id is not None:
                return get_immich_photo_url(asset_id)
        elif (
            kind
            in {
                ModificationKind.CREATE_ALBUM,
                ModificationKind.DELETE_ALBUM,
                ModificationKind.RENAME_ALBUM,
            }
            and album_wrapper is not None
        ):
            if hasattr(album_wrapper, "get_immich_album_url"):
                return album_wrapper.get_immich_album_url()
        return None

    @typechecked
    def _format_modification_entry(self, entry: ModificationEntry) -> str:
        # Serialize first and delegate formatting to the serializable class
        serializable = entry.to_serializable()
        return serializable.to_log_string()
