from __future__ import annotations

from threading import Lock
from typing import Dict, List, Set
from uuid import UUID

import attrs
from immich_client.models.bulk_ids_dto import BulkIdsDto
from typeguard import typechecked

from immich_autotag.assets.asset_response_wrapper import AssetResponseWrapper
from immich_autotag.assets.asset_validation import \
    validate_and_update_asset_classification
# Date correction config flag
from immich_autotag.config.user import (ALBUM_PATTERN, ENABLE_DATE_CORRECTION,
                                        TAG_CONVERSIONS, VERBOSE_LOGGING)
from immich_autotag.logging.utils import log_debug
from immich_autotag.report.modification_report import ModificationReport
from immich_autotag.tags.modification_kind import ModificationKind


# Date correction logic
@attrs.define(auto_attribs=True, slots=True, frozen=True)
class DuplicateAlbumsInfo:
    # Maps asset UUID to AssetResponseWrapper
    _mapping: Dict[UUID, AssetResponseWrapper]

    def all_album_names(self) -> set[str]:
        """Return a set with all album names found among duplicates."""
        return {
            album
            for wrapper in self._mapping.values()
            for album in wrapper.get_album_names()
        }

    def get_details(self) -> Dict[UUID, AssetResponseWrapper]:
        """Return the full mapping (read-only)."""
        return dict(self._mapping)


@typechecked
def get_album_from_duplicates(
    asset_wrapper: "AssetResponseWrapper",
) -> DuplicateAlbumsInfo:
    """
    For a given asset, if it is a duplicate, returns a DuplicateAlbumsInfo object encapsulating the mapping from each duplicate AssetResponseWrapper (excluding itself)
    to the list of album names it belongs to. This allows for richer traceability and future extensibility.
    If there are no duplicates, returns an empty mapping.
    """
    result: Dict[UUID, AssetResponseWrapper] = {}
    duplicate_wrappers = asset_wrapper.get_duplicate_wrappers()
    for dup_wrapper in duplicate_wrappers:
        result[dup_wrapper.id_as_uuid] = dup_wrapper
    return DuplicateAlbumsInfo(result)


import attrs


@attrs.define(auto_attribs=True, slots=True, frozen=True)
class AlbumDecision:
    """
    Encapsulates the decision logic for album assignment, including all album info from duplicates (as DuplicateAlbumsInfo)
    and the album detected from folder structure (if any).
    """

    duplicates_info: DuplicateAlbumsInfo
    album_from_folder: str | None

    def __attrs_post_init__(self):
        # Place breakpoint here for debugging construction
        pass

    def all_options(self) -> set[str]:
        import re

        from immich_autotag.config.user import ALBUM_PATTERN

        opts = set(self.duplicates_info.all_album_names())
        opts = {a for a in opts if re.match(ALBUM_PATTERN, a)}
        if self.album_from_folder:
            opts.add(self.album_from_folder)
        # Only return albums that match the event pattern
        return opts

    def valid_albums(self) -> set[str]:
        import re

        return {a for a in self.all_options() if re.match(ALBUM_PATTERN, a)}

    def is_unique(self) -> bool:
        valid = self.valid_albums()
        return len(valid) == 1

    def has_conflict(self) -> bool:
        valid = self.valid_albums()
        return len(valid) > 1

    def get_unique(self) -> str | None:
        valid = self.valid_albums()
        if len(valid) == 1:
            return next(iter(valid))
        return None

    def get_album_origin(self, album: str) -> str:
        if self.album_from_folder == album:
            return "from folders"
        elif album in self.duplicates_info.all_album_names():
            return "from duplicates"
        else:
            return "unknown"

    def __str__(self):
        return f"AlbumDecision(valid={self.valid_albums()}, folder={self.album_from_folder})"


@typechecked
def decide_album_for_asset(asset_wrapper: "AssetResponseWrapper") -> AlbumDecision:
    """
    Returns an AlbumDecision object with all relevant information to decide the album.
    """
    albums_info = get_album_from_duplicates(asset_wrapper)
    detected_album = asset_wrapper.try_detect_album_from_folders()
    return AlbumDecision(duplicates_info=albums_info, album_from_folder=detected_album)


@typechecked
def analyze_and_assign_album(
    asset_wrapper: "AssetResponseWrapper",
    tag_mod_report: "ModificationReport",
    suppress_album_already_belongs_log: bool = True,
    fail_on_duplicate_album_conflict: bool = False,
    verbose: bool = VERBOSE_LOGGING,
) -> None:
    """
    Handles all logic related to analyzing potential albums for an asset, deciding assignment, and handling conflicts.
    """
    album_decision = decide_album_for_asset(asset_wrapper)
    # If there is an album conflict among duplicates, add the conflict tag; otherwise, remove it if present
    conflict = album_decision.has_conflict()
    duplicate_id = asset_wrapper.asset.duplicate_id
    # Apply the conflict tag logic to all duplicates
    all_wrappers = [asset_wrapper] + list(
        album_decision.duplicates_info.get_details().values()
    )
    for wrapper in all_wrappers:
        wrapper.ensure_autotag_duplicate_album_conflict(
            conflict, duplicate_id=duplicate_id
        )

    from immich_autotag.logging.levels import LogLevel
    from immich_autotag.logging.utils import log

    asset_name = asset_wrapper.original_file_name
    asset_id = asset_wrapper.id
    immich_url = asset_wrapper.get_immich_photo_url().geturl()
    if album_decision.is_unique():
        detected_album = album_decision.get_unique()
        if detected_album:
            album_origin = album_decision.get_album_origin(detected_album)
            log(
                f"[ALBUM ASSIGNMENT] Asset '{asset_name}' will be assigned to album '{detected_album}' (origin: {album_origin}).",
                level=LogLevel.FOCUS,
            )
            _process_album_detection(
                asset_wrapper,
                tag_mod_report,
                detected_album,
                album_origin,
                suppress_album_already_belongs_log=suppress_album_already_belongs_log,
            )
        else:
            log(
                f"[ALBUM ASSIGNMENT] No valid album found for asset '{asset_name}'. No assignment performed.",
                level=LogLevel.FOCUS,
            )
    elif conflict:
        albums_info = album_decision.duplicates_info
        log(
            f"[ALBUM ASSIGNMENT] Asset '{asset_name}' not assigned to any album due to conflict: multiple valid album options {album_decision.valid_albums()}\nSee asset: {immich_url}",
            level=LogLevel.FOCUS,
        )
        details = []
        for _, dup_wrapper in albums_info.get_details().items():
            albums = dup_wrapper.get_album_names()
            details.append(
                f"{dup_wrapper.get_link().geturl()} | file: {dup_wrapper.asset.original_file_name} | date: {dup_wrapper.asset.created_at} | albums: {albums or '[unavailable]'}"
            )
        if details:
            log(
                f"[ALBUM ASSIGNMENT] Duplicates of {asset_wrapper.uuid}:\n"
                + "\n".join(details),
                level=LogLevel.FOCUS,
            )
        if fail_on_duplicate_album_conflict:
            raise NotImplementedError(
                f"Ambiguous album assignment for asset {asset_id}: multiple valid albums {album_decision.valid_albums()}\nSee asset: {immich_url}\nDuplicates: {', '.join(details) if details else '-'}"
            )
        # No assignment performed debido a ambigüedad/conflicto
        return
    else:
        log(
            f"[ALBUM ASSIGNMENT] Asset '{asset_name}' was not assigned to any album. No valid or conflicting options found.",
            level=LogLevel.FOCUS,
        )


# Public API of the subpackage for duplicate tag logic (located inside assets)
from immich_autotag.assets.duplicate_tag_logic.analyze_duplicate_classification_tags import \
    analyze_duplicate_classification_tags


@typechecked
def process_single_asset(
    asset_wrapper: "AssetResponseWrapper",
    tag_mod_report: "ModificationReport",
    lock: Lock,
    suppress_album_already_belongs_log: bool = True,
) -> None:
    log_debug(f"[BUG] INICIO process_single_asset {getattr(asset_wrapper, 'id', None)}")
    from immich_autotag.logging.levels import LogLevel
    from immich_autotag.logging.utils import log

    log(
        f"[DEBUG] [process_single_asset] INICIO asset_id={getattr(asset_wrapper, 'id', None)}",
        level=LogLevel.FOCUS,
    )
    try:
        log("[DEBUG] Obteniendo URL del asset...", level=LogLevel.FOCUS)
        asset_url = asset_wrapper.get_immich_photo_url().geturl()
    except Exception as e:
        asset_name = (
            getattr(asset_wrapper, "original_file_name", None)
            or getattr(asset_wrapper, "filename", None)
            or "[sin nombre]"
        )
        from pprint import pformat

        details = pformat(vars(asset_wrapper))
        log(
            f"[ERROR] No se pudo obtener la URL Immich del asset. Nombre: {asset_name}\nDetalles: {details}",
            level=LogLevel.FOCUS,
        )
        raise RuntimeError(
            f"Could not obtain Immich URL for asset. Name: {asset_name}. Exception: {e}\nDetails: {details}"
        )
    asset_name = asset_wrapper.original_file_name
    if not asset_name:
        asset_name = "[sin nombre]"
    log(f"Procesando asset: {asset_url} | Nombre: {asset_name}", level=LogLevel.FOCUS)

    log("[DEBUG] Aplicando conversiones de tags...", level=LogLevel.FOCUS)
    asset_wrapper.apply_tag_conversions(TAG_CONVERSIONS)

    if ENABLE_DATE_CORRECTION:
        log("[DEBUG] Corrigiendo fecha del asset...", level=LogLevel.FOCUS)
        from immich_autotag.assets.date_correction.core_logic import \
            correct_asset_date

        correct_asset_date(asset_wrapper)

    log(
        "[DEBUG] Analizando tags de clasificación de duplicados...",
        level=LogLevel.FOCUS,
    )
    analyze_duplicate_classification_tags(asset_wrapper)

    log("[DEBUG] Analizando y asignando álbum...", level=LogLevel.FOCUS)
    analyze_and_assign_album(
        asset_wrapper, tag_mod_report, suppress_album_already_belongs_log
    )

    log(
        "[DEBUG] Validando y actualizando clasificación del asset...",
        level=LogLevel.FOCUS,
    )
    validate_and_update_asset_classification(
        asset_wrapper,
        tag_mod_report=tag_mod_report,
    )

    log(
        "[DEBUG] Intentando adquirir lock para flush del reporte...",
        level=LogLevel.FOCUS,
    )
    with lock:
        log(
            "[DEBUG] Lock adquirido, haciendo flush del reporte...",
            level=LogLevel.FOCUS,
        )
        tag_mod_report.flush()
    # Actualiza los contadores totales de etiquetas de salida para este asset
    from immich_autotag.statistics.statistics_manager import StatisticsManager
    StatisticsManager.get_instance().process_asset_tags(asset_wrapper.get_tag_names())
    log(
        f"[DEBUG] [process_single_asset] FIN asset_id={getattr(asset_wrapper, 'id', None)}",
        level=LogLevel.FOCUS,
    )


@typechecked
def _process_album_detection(
    asset_wrapper: "AssetResponseWrapper",
    tag_mod_report: "ModificationReport",
    detected_album: str,
    album_origin: str,
    suppress_album_already_belongs_log: bool = True,
) -> None:
    from immich_autotag.logging.levels import LogLevel
    from immich_autotag.logging.utils import log

    # Log candidate album always at FOCUS level
    log(
        f"[ALBUM CHECK] Asset '{asset_wrapper.original_file_name}' candidate album: '{detected_album}' (origin: {album_origin})",
        level=LogLevel.FOCUS,
    )
    from immich_client.api.albums import add_assets_to_album
    from immich_client.models.albums_add_assets_dto import AlbumsAddAssetsDto

    client = asset_wrapper.context.client
    albums_collection = asset_wrapper.context.albums_collection
    album_wrapper = albums_collection.create_or_get_album_with_user(
        detected_album, client, tag_mod_report=tag_mod_report
    )
    album = album_wrapper.album
    if asset_wrapper.id not in [a.id for a in album.assets or []]:
        log(
            f"[ALBUM ASSIGNMENT] Asset '{asset_wrapper.original_file_name}' assigned to album '{detected_album}' (origin: {album_origin})",
            level=LogLevel.FOCUS,
        )
        album_wrapper.add_asset(asset_wrapper, client, tag_mod_report=tag_mod_report)
    else:
        log(
            f"[ALBUM ASSIGNMENT] Asset '{asset_wrapper.original_file_name}' already in album '{detected_album}' (origin: {album_origin}), no action taken.",
            level=LogLevel.FOCUS,
        )
