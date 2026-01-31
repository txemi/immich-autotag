from __future__ import annotations

import attr
from typeguard import typechecked


@typechecked
@attr.s(auto_attribs=True, slots=True)
class TagStatsManager:
    stats_manager: "StatisticsManager" = attr.ib(repr=False)
    _stats_manager: "StatisticsManager" = attr.ib(init=False, repr=False)

    def __attrs_post_init__(self):
        # Runtime type check to enforce type safety without circular import
        from .statistics_manager import StatisticsManager as SM

        self._stats_manager = self.stats_manager
        if not isinstance(self._stats_manager, SM):
            raise TypeError(
                f"_stats_manager must be a StatisticsManager, got {type(self._stats_manager)}"
            )

    @typechecked
    def process_asset_tags(self, tag_names: list[str]) -> None:
        stats = self._stats_manager.get_stats()
        for tag in self._stats_manager.get_relevant_tags():
            if tag in tag_names:
                if tag not in stats.output_tag_counters:
                    from .run_statistics import OutputTagCounter

                    stats.output_tag_counters[tag] = OutputTagCounter()
                stats.output_tag_counters[tag].total += 1
        self._stats_manager.save_to_file()

    @typechecked
    def increment_tag_added(self, tag: "TagWrapper") -> None:
        tag_name = tag.get_name()
        if tag_name in self._stats_manager.get_relevant_tags():
            stats = self._stats_manager.get_stats()
            if tag_name not in stats.output_tag_counters:
                from .run_statistics import OutputTagCounter

                stats.output_tag_counters[tag_name] = OutputTagCounter()
            stats.output_tag_counters[tag_name].added += 1
            self._stats_manager.save_to_file()

    @typechecked
    def increment_tag_removed(self, tag: "TagWrapper") -> None:
        try:
            tag_name = tag.get_name()
        except AttributeError:
            raise TypeError(
                f"increment_tag_removed expects TagWrapper, got {type(tag)}: {tag}"
            )
        if tag_name in self._stats_manager.get_relevant_tags():
            stats = self._stats_manager.get_stats()
            if tag_name not in stats.output_tag_counters:
                from .run_statistics import OutputTagCounter

                stats.output_tag_counters[tag_name] = OutputTagCounter()
            stats.output_tag_counters[tag_name].removed += 1
            self._stats_manager.save_to_file()

    @typechecked
    def _increment_album_date_mismatch(self) -> None:
        stats = self._stats_manager.get_stats()
        try:
            stats.album_date_mismatch_count += 1
        except AttributeError:
            stats.album_date_mismatch_count = 1

    @typechecked
    def _increment_tag_error(self, tag: "TagWrapper") -> None:
        tag_name = tag.get_name()
        stats = self._stats_manager.get_stats()
        if tag_name not in stats.output_tag_counters:
            from .run_statistics import OutputTagCounter

            stats.output_tag_counters[tag_name] = OutputTagCounter()
        stats.output_tag_counters[tag_name].errors += 1
        self._stats_manager.save_to_file()

    @typechecked
    def _increment_asset_date_update(self) -> None:
        stats = self._stats_manager.get_stats()
        stats.update_asset_date_count += 1
        self._stats_manager.save_to_file()

    @typechecked
    def _increment_album_assignment(self, album: "AlbumResponseWrapper | None") -> None:
        if album is not None:
            from immich_autotag.albums.album.album_response_wrapper import (
                AlbumResponseWrapper,
            )

            assert isinstance(album, AlbumResponseWrapper)
            album_name = album.get_album_name()
            stats = self._stats_manager.get_stats()
            if album_name not in stats.output_album_counters:
                from .run_statistics import OutputAlbumCounter

                stats.output_album_counters[album_name] = OutputAlbumCounter()
            stats.output_album_counters[album_name].assigned += 1
            stats.output_album_counters[album_name].total += 1
            self._stats_manager.save_to_file()
        else:
            raise RuntimeError(
                "AlbumResponseWrapper is required to count ASSIGN_ASSET_TO_ALBUM"
            )

    @typechecked
    def increment_tag_action(
        self,
        tag: "TagWrapper",
        kind: "ModificationKind",
        album: "AlbumResponseWrapper | None",
    ) -> None:
        from immich_autotag.report.modification_kind import ModificationKind

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
