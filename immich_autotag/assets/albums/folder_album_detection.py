"""Album detection from an asset's folder, without writing anything.

`AssetResponseWrapper.try_detect_album_from_folders` uses this and then keeps the
album detection conflict tag in step. Code that only needs to know the folder
album of an asset (for example, of the other copies of a duplicate group) calls
`folder_album_of` and writes nothing.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from immich_autotag.albums.folder_analysis.album_folder_analyzer import (
    AlbumFolderAnalyzer,
)
from immich_autotag.config.manager import ConfigManager

if TYPE_CHECKING:
    from immich_autotag.assets.asset_response_wrapper import AssetResponseWrapper


def folder_analyzer_for(asset: "AssetResponseWrapper") -> AlbumFolderAnalyzer | None:
    """The folder analyzer of the asset, or None when folder detection does not apply.

    It applies only if album detection from folders is enabled, the asset is
    unclassified and it is not already in an album matching the rules.
    """
    from immich_autotag.classification.classification_rule_set import (
        ClassificationRuleSet,
    )
    from immich_autotag.classification.classification_status import (
        ClassificationStatus,
    )

    config = ConfigManager.get_instance().get_config()
    if not config.album_detection_from_folders.enabled:
        return None
    status = asset.get_classification_status().classification_status()
    match status:
        case ClassificationStatus.UNCLASSIFIED:
            pass
        case ClassificationStatus.CLASSIFIED | ClassificationStatus.CONFLICT:
            return None
        case _:
            raise NotImplementedError(f"Unhandled classification status: {status}")
    rule_set = ClassificationRuleSet.get_rule_set_from_config_manager()
    if rule_set.matches_any_album_of_asset(asset):
        return None
    return AlbumFolderAnalyzer(asset.get_original_path())


def folder_album_of(asset: "AssetResponseWrapper") -> str | None:
    """The album the asset's folder points to, or None. Writes nothing."""
    analyzer = folder_analyzer_for(asset)
    return analyzer.get_album_name() if analyzer is not None else None
