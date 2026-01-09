from typing import TYPE_CHECKING

import attr
from typeguard import typechecked

if TYPE_CHECKING:
    from immich_autotag.albums.album_response_wrapper import AlbumResponseWrapper
    from immich_autotag.tags.modification_kind import ModificationKind
    from immich_autotag.tags.tag_response_wrapper import TagWrapper

    from .statistics_manager import StatisticsManager


@typechecked
@attr.s(auto_attribs=True, kw_only=True)
class TagStatsManager:
    stats_manager: "StatisticsManager" = attr.ib(
        validator=attr.validators.instance_of(object)
    )

    @stats_manager.validator
    def _validate_stats_manager(self, attribute, value):
        from .statistics_manager import StatisticsManager

        if not isinstance(value, StatisticsManager):
            raise TypeError(
                f"stats_manager must be a StatisticsManager, got {type(value)}"
            )

    @typechecked
    def process_asset_tags(self, tag_names: list[str]) -> None:
        stats = self.stats_manager.get_stats()
        for tag in self.stats_manager.RELEVANT_TAGS:
            if tag in tag_names:
                if tag not in stats.output_tag_counters:
                    from .run_statistics import OutputTagCounter

                    stats.output_tag_counters[tag] = OutputTagCounter()
                stats.output_tag_counters[tag].total += 1
        self.stats_manager._save_to_file()

    @typechecked
    def increment_tag_added(self, tag: "TagWrapper") -> None:
        tag_name = tag.name
        if tag_name in self.stats_manager.RELEVANT_TAGS:
            stats = self.stats_manager.get_stats()
            if tag_name not in stats.output_tag_counters:
                from .run_statistics import OutputTagCounter

                stats.output_tag_counters[tag_name] = OutputTagCounter()
            stats.output_tag_counters[tag_name].added += 1
            self.stats_manager._save_to_file()

    @typechecked
    def increment_tag_removed(self, tag: "TagWrapper") -> None:
        if not hasattr(tag, "name"):
            raise TypeError(
                f"increment_tag_removed expects TagWrapper, got {type(tag)}: {tag}"
            )
        tag_name = tag.name
        if tag_name in self.stats_manager.RELEVANT_TAGS:
            stats = self.stats_manager.get_stats()
            if tag_name not in stats.output_tag_counters:
                from .run_statistics import OutputTagCounter

                stats.output_tag_counters[tag_name] = OutputTagCounter()
            stats.output_tag_counters[tag_name].removed += 1
            self.stats_manager._save_to_file()

    @typechecked
    def increment_tag_action(
        self,
        tag: "TagWrapper",
        kind: "ModificationKind",
        album: "AlbumResponseWrapper | None",
    ) -> None:
        from immich_autotag.tags.modification_kind import ModificationKind

        if kind == ModificationKind.ADD_TAG_TO_ASSET:
            self.increment_tag_added(tag)
        elif kind == ModificationKind.REMOVE_TAG_FROM_ASSET:
            self.increment_tag_removed(tag)
        elif kind == ModificationKind.WARNING_TAG_REMOVAL_FROM_ASSET_FAILED:
            self._increment_tag_error(tag)
        elif kind == ModificationKind.UPDATE_ASSET_DATE:
            self._increment_asset_date_update()
        elif kind == ModificationKind.ASSIGN_ASSET_TO_ALBUM:
            self._increment_album_assignment(album)
        elif kind == ModificationKind.ALBUM_DATE_MISMATCH:
            self._increment_album_date_mismatch()
        else:
            raise NotImplementedError(
                f"increment_tag_action not implemented for ModificationKind: {kind}"
            )

    @typechecked
    def _increment_album_date_mismatch(self) -> None:
        stats = self.stats_manager.get_stats()
        if not hasattr(stats, "album_date_mismatch_count"):
            stats.album_date_mismatch_count = 0
        stats.album_date_mismatch_count += 1

    @typechecked
    def _increment_tag_error(self, tag: "TagWrapper") -> None:
        tag_name = tag.name
        stats = self.stats_manager.get_stats()
        if tag_name not in stats.output_tag_counters:
            from .run_statistics import OutputTagCounter

            stats.output_tag_counters[tag_name] = OutputTagCounter()
        stats.output_tag_counters[tag_name].errors += 1
        self.stats_manager._save_to_file()

    @typechecked
    def _increment_asset_date_update(self) -> None:
        stats = self.stats_manager.get_stats()
        stats.update_asset_date_count += 1
        self.stats_manager._save_to_file()

    @typechecked
    def _increment_album_assignment(self, album: "AlbumResponseWrapper | None") -> None:
        if album is not None:
            from immich_autotag.albums.album_response_wrapper import (
                AlbumResponseWrapper,
            )

            assert isinstance(album, AlbumResponseWrapper)
            album_name = album.album.album_name
            stats = self.stats_manager.get_stats()
            if album_name not in stats.output_album_counters:
                from .run_statistics import OutputAlbumCounter

                stats.output_album_counters[album_name] = OutputAlbumCounter()
            stats.output_album_counters[album_name].assigned += 1
            stats.output_album_counters[album_name].total += 1
            self.stats_manager._save_to_file()
        else:
            raise RuntimeError(
                "AlbumResponseWrapper is required to count ASSIGN_ASSET_TO_ALBUM"
            )
