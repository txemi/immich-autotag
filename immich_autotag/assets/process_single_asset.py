from __future__ import annotations
from typing import Set

from threading import Lock

from immich_client.models.bulk_ids_dto import BulkIdsDto
from typeguard import typechecked

from immich_autotag.assets.asset_response_wrapper import AssetResponseWrapper
from immich_autotag.tags.tag_modification_report import TagModificationReport
from immich_autotag.assets.asset_validation import validate_and_update_asset_classification
from immich_autotag.config.user import TAG_CONVERSIONS, ALBUM_PATTERN

@typechecked
def get_album_from_duplicates(asset_wrapper: "AssetResponseWrapper") -> Set[str]:
    """
    Si el asset es un duplicado, busca si alguno de sus duplicados ya tiene álbum y devuelve el conjunto de todos los álbumes encontrados.
    Si no hay duplicados con álbum, devuelve un set vacío.
    """
    from uuid import UUID
    context = asset_wrapper.context
    duplicate_id = asset_wrapper.asset.duplicate_id
    albums_for_duplicates = set()
    if duplicate_id is not None:
        group = context.duplicates_collection.get_group(UUID(duplicate_id))
        albums_collection = context.albums_collection
        for dup_id in group:
            # Saltar el propio asset
            if str(dup_id) == asset_wrapper.asset.id:
                continue
            dup_asset = context.asset_manager.get_asset(dup_id, context)
            if dup_asset is not None:
                albums = albums_collection.albums_for_asset(dup_asset.asset)
                albums_for_duplicates.update(albums)
    return albums_for_duplicates


import attrs
@attrs.define(auto_attribs=True, slots=True, frozen=True)

class AlbumDecision:
    albums_from_duplicates: set[str]
    album_from_folder: str | None

    def all_options(self) -> set[str]:
        opts = set(self.albums_from_duplicates)
        if self.album_from_folder:
            opts.add(self.album_from_folder)
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
        elif album in self.albums_from_duplicates:
            return "from duplicates"
        else:
            return "unknown"

    def __str__(self):
        return f"AlbumDecision(valid={self.valid_albums()}, folder={self.album_from_folder})"


@typechecked
def decide_album_for_asset(asset_wrapper: "AssetResponseWrapper") -> AlbumDecision:
    """
    Devuelve un objeto AlbumDecision con toda la información relevante para decidir el álbum.
    """
    import re
    albums_from_duplicates = get_album_from_duplicates(asset_wrapper)
    # Filtrar solo los que cumplen el patrón
    filtered_duplicates = {a for a in albums_from_duplicates if re.match(ALBUM_PATTERN, a)}
    detected_album = asset_wrapper.try_detect_album_from_folders()
    return AlbumDecision(albums_from_duplicates=filtered_duplicates, album_from_folder=detected_album)
@typechecked

def process_single_asset(
    asset_wrapper: "AssetResponseWrapper",
    tag_mod_report: "TagModificationReport",
    lock: Lock,
) -> None:
    album_decision = decide_album_for_asset(asset_wrapper)
    if album_decision.is_unique():
        detected_album = album_decision.get_unique()
        if detected_album:
            album_origin = album_decision.get_album_origin(detected_album)
            _process_album_detection(asset_wrapper, tag_mod_report, detected_album, album_origin)
    elif album_decision.has_conflict():
        print(f"[ALBUM DECISION] Asset {asset_wrapper.asset.id} tiene múltiples opciones de álbum válidos: {album_decision.valid_albums()}")
        raise NotImplementedError(f"No se ha implementado la lógica para decidir entre múltiples álbumes válidos: {album_decision}")
    # Si no hay álbum válido, no se asigna ninguno
    asset_wrapper.apply_tag_conversions(TAG_CONVERSIONS, tag_mod_report=tag_mod_report)
    validate_and_update_asset_classification(
        asset_wrapper,
        tag_mod_report=tag_mod_report,
    )
    with lock:
        tag_mod_report.flush()

@typechecked
def _process_album_detection(
    asset_wrapper: "AssetResponseWrapper",
    tag_mod_report: "TagModificationReport",
    detected_album: str,
    album_origin: str,
) -> None:
    print(
        f"[ALBUM DETECTION] Asset '{asset_wrapper.original_file_name}' candidate album: '{detected_album}' ({album_origin})"
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
        print(
            f"[ALBUM DETECTION] Adding asset '{asset_wrapper.original_file_name}' to album '{detected_album}'..."
        )
        try:
            result = add_assets_to_album.sync(
                id=album.id,
                client=client,
                body=BulkIdsDto(ids=[asset_wrapper.id]),
            )
        except Exception as e:
            print(f"[ERROR] Exception when adding asset to album: {e}")
            raise
        # Validación estricta del resultado
        if not isinstance(result, list):
            print(f"[ERROR] Unexpected return type from add_assets_to_album: {type(result)}")
            raise RuntimeError("add_assets_to_album did not return a list")
        found = False
        for item in result:
            # Comprobación estricta de atributos sin hasattr ni getattr
            try:
                _id = item.id
                _success = item.success
            except AttributeError:
                raise RuntimeError(f"Item in add_assets_to_album response missing required attributes: {item}")
            if _id == str(asset_wrapper.id):
                found = True
                if not _success:
                    # El atributo error puede no estar siempre, pero si está lo mostramos
                    error_msg = None
                    try:
                        error_msg = item.error
                    except AttributeError:
                        pass
                    print(f"[ERROR] Asset {asset_wrapper.id} was not successfully added to album {album.id}: {error_msg}")
                    raise RuntimeError(f"Asset {asset_wrapper.id} was not successfully added to album {album.id}")
        if not found:
            print(f"[ERROR] Asset {asset_wrapper.id} not found in add_assets_to_album response for album {album.id}")
            raise RuntimeError(f"Asset {asset_wrapper.id} not found in add_assets_to_album response")
        tag_mod_report.add_assignment_modification(
            action="assign",
            asset_id=asset_wrapper.id,
            asset_name=asset_wrapper.original_file_name,
            album_id=album.id,
            album_name=detected_album,
        )
    else:
        print(
            f"[ALBUM DETECTION] Asset already belongs to album '{detected_album}'"
        )
