"""
Module for auditing and reporting entity modifications (tags, albums, assets, etc.)

TODO: The name of this class ('ModificationReport') does not accurately reflect its current function. It now records not only modifications but also warnings and general events.
    It should be renamed to something more generic in the future as it also reports warnings and relevant circumstances in a structured way.
"""

from __future__ import annotations

import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional
from urllib.parse import ParseResult

import attrs

from immich_autotag.utils.run_output_dir import get_run_output_dir

if TYPE_CHECKING:
    from immich_autotag.albums.album.album_response_wrapper import AlbumResponseWrapper
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
    import threading

    _lock: threading.Lock = attrs.field(
        default=attrs.Factory(threading.Lock), init=False, repr=False
    )

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
        # Account for the event in the statistics manager
        from immich_autotag.statistics.statistics_manager import StatisticsManager

        StatisticsManager.get_instance().increment_event(kind, extra_key=tag)
        # Local import to avoid circularity
        if album is not None:
            from immich_autotag.albums.album.album_response_wrapper import (
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
                from immich_autotag.logging.levels import LogLevel
                from immich_autotag.logging.utils import log

                log(
                    f"Could not clear the tag modification report: {e}",
                    level=LogLevel.WARNING,
                )
            self._cleared_report = True

        # If user is None, obtain it from the singleton ImmichContext
        user_instance = user
        if user_instance is None:
            from immich_autotag.context.immich_context import ImmichContext

            context = ImmichContext.get_instance()
            user_instance = UserResponseWrapper.from_context(context)

        # Calculate progress using StatisticsManager (without try/except)
        from immich_autotag.statistics.statistics_manager import StatisticsManager

        stats_manager = StatisticsManager.get_instance()
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
        if tag is not None:
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
        from immich_autotag.statistics.statistics_manager import StatisticsManager

        StatisticsManager.get_instance().increment_event(kind, extra_key=tag)
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
        # Centraliza el log aquí si corresponde
        from immich_autotag.logging.utils import log
        level = kind.log_level
        # Mensajes por tipo
        if kind == ModificationKind.DELETE_ALBUM:
            msg = f"[DELETE_ALBUM] Album '{album.get_album_name()}' (id={album.get_album_id()}) deleted. Reason: {extra.get('reason') if extra else ''}"
        elif kind == ModificationKind.CREATE_ALBUM:
            msg = f"[CREATE_ALBUM] Album '{album.get_album_name()}' (id={album.get_album_id()}) created."
        elif kind == ModificationKind.RENAME_ALBUM:
            msg = f"[RENAME_ALBUM] Album '{album.get_album_name()}' (id={album.get_album_id()}) renamed from '{old_value}' to '{new_value}'."
        else:
            msg = f"[ALBUM_MODIFICATION] Album '{album.get_album_name()}' (id={album.get_album_id()}) modification: {kind.name}"
        log(msg, level=level)
        from immich_autotag.statistics.statistics_manager import StatisticsManager

        StatisticsManager.get_instance().increment_event(kind)
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
        extra: Optional[dict] = None,
    ) -> None:
        assert kind in {
            ModificationKind.ASSIGN_ASSET_TO_ALBUM,
            ModificationKind.REMOVE_ASSET_FROM_ALBUM,
            ModificationKind.WARNING_ASSET_ALREADY_IN_ALBUM,
        }
        from immich_autotag.statistics.statistics_manager import StatisticsManager

        StatisticsManager.get_instance().increment_event(kind)
        self.add_modification(
            kind=kind,
            asset_wrapper=asset_wrapper,
            album=album,
            user=user,
            extra=extra,
        )

    @typechecked
    def add_error_modification(
        self,
        kind: ModificationKind,
        asset_wrapper: Optional["AssetResponseWrapper"] = None,
        error_message: Optional[str] = None,
        error_category: Optional[str] = None,
        extra: Optional[dict] = None,
    ) -> None:
        """Records a recoverable error event for tracking failed assets.

        Args:
            kind: Error type (e.g., ERROR_ALBUM_NOT_FOUND, ERROR_ASSET_DELETED, etc.)
            asset_wrapper: The asset that failed processing
            error_message: The error message from the exception
            error_category: Category like "Recoverable (API 400 - Resource not found)"
            extra: Additional context (e.g., album_id, retry_count)
        """
        assert kind in {
            ModificationKind.ERROR_ASSET_SKIPPED_RECOVERABLE,
            ModificationKind.ERROR_ALBUM_NOT_FOUND,
            ModificationKind.ERROR_PERMISSION_DENIED,
            ModificationKind.ERROR_ASSET_DELETED,
            ModificationKind.ERROR_NETWORK_TEMPORARY,
        }
        # Merge error details into extra dict
        if extra is None:
            extra = {}
        if error_message:
            extra["error_message"] = error_message
        if error_category:
            extra["error_category"] = error_category

        from immich_autotag.statistics.statistics_manager import StatisticsManager

        StatisticsManager.get_instance().increment_event(kind)
        self.add_modification(
            kind=kind,
            asset_wrapper=asset_wrapper,
            extra=extra,
        )

    @typechecked
    def add_album_permission_modification(
        self,
        kind: ModificationKind,
        album: Optional["AlbumResponseWrapper"] = None,
        matched_rules: Optional[list[str]] = None,
        groups: Optional[list[str]] = None,
        members: Optional[list[str]] = None,
        access_level: Optional[str] = None,
        extra: Optional[dict] = None,
    ) -> None:
        """Records album permission events (detection, sharing, failures).

        Args:
            kind: Event type (e.g., ALBUM_PERMISSION_RULE_MATCHED, ALBUM_PERMISSION_SHARED, ALBUM_PERMISSION_REMOVED)
            album: The album being processed
            matched_rules: List of rule names that matched
            groups: List of group names to share with
            members: List of member emails/IDs
            access_level: Permission level (view/edit/admin)
            extra: Additional context
        """
        assert kind in {
            ModificationKind.ALBUM_PERMISSION_RULE_MATCHED,
            ModificationKind.ALBUM_PERMISSION_GROUPS_RESOLVED,
            ModificationKind.ALBUM_PERMISSION_NO_MATCH,
            ModificationKind.ALBUM_PERMISSION_SHARED,
            ModificationKind.ALBUM_PERMISSION_REMOVED,
            ModificationKind.ALBUM_PERMISSION_SHARE_FAILED,
        }
        if extra is None:
            extra = {}
        if matched_rules:
            extra["matched_rules"] = matched_rules
        if groups:
            extra["groups"] = groups
        if members:
            extra["members"] = members
        if access_level:
            extra["access_level"] = access_level

        from immich_autotag.statistics.statistics_manager import StatisticsManager

        StatisticsManager.get_instance().increment_event(kind)
        self.add_modification(
            kind=kind,
            album=album,
            extra=extra,
        )

    @typechecked
    def flush(self) -> None:
        """Flushes the report to file (append), thread-safe."""
        if not self.modifications or self._since_last_flush == 0:
            return
        import os

        with self._lock:
            os.makedirs(os.path.dirname(self.report_path), exist_ok=True)
            with open(self.report_path, "a", encoding="utf-8") as f:
                for entry in self.modifications[-self._since_last_flush :]:
                    f.write(self._format_modification_entry(entry) + "\n")
            self._since_last_flush = 0

    @typechecked
    def print_summary(self) -> None:
        from immich_autotag.logging.levels import LogLevel
        from immich_autotag.logging.utils import log

        log("[SUMMARY] Modifications:", level=LogLevel.INFO)
        for entry in self.modifications:
            log(self._format_modification_entry(entry), level=LogLevel.INFO)
        log(f"Total modifications: {len(self.modifications)}", level=LogLevel.INFO)

    @typechecked
    def _build_link(
        self,
        kind: ModificationKind,
        asset_wrapper: Any = None,
        album_wrapper: Any = None,
    ) -> Optional["ParseResult"]:
        # Account for the event in the statistics manager
        from immich_autotag.statistics.statistics_manager import StatisticsManager

        StatisticsManager.get_instance().increment_event(kind)
        """
        Build a link for the modification entry based on kind and wrappers.
        """

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
            # The URL must be obtainable for an asset. Do not swallow errors here —
            # let exceptions surface so the failure can be noticed and fixed.
            return asset_wrapper.get_immich_photo_url()
        elif (
            kind
            in {
                ModificationKind.CREATE_ALBUM,
                ModificationKind.DELETE_ALBUM,
                ModificationKind.RENAME_ALBUM,
            }
            and album_wrapper is not None
        ):
            # The album URL must be obtainable; do not swallow exceptions here.
            return album_wrapper.get_immich_album_url()
        return None

    @typechecked
    def _format_modification_entry(self, entry: ModificationEntry) -> str:
        # Serialize first and delegate formatting to the serializable class
        serializable = entry.to_serializable()
        return serializable.to_log_string()
