# get_asset_date_sources.py
# Función: get_asset_date_sources
from immich_autotag.assets.asset_response_wrapper import AssetResponseWrapper
from immich_autotag.assets.date_correction.asset_date_sources import AssetDateSources
from immich_autotag.assets.date_correction.extract_whatsapp_date_from_path import extract_whatsapp_date_from_path
from immich_autotag.assets.date_correction.asset_date_candidate import AssetDateCandidate
from immich_autotag.assets.date_correction.date_source_kind import DateSourceKind


def get_asset_date_sources(asset_wrapper: AssetResponseWrapper) -> AssetDateSources:
    """
    Extract all relevant date sources for a given asset.
    Returns an AssetDateSources object with immich_date, WhatsApp filename date, and WhatsApp path date.
    """
    # IMMICH date
    immich_dt = asset_wrapper.get_best_date()
    immich_candidate = None
    if immich_dt:
        immich_candidate = AssetDateCandidate(
            source_kind=DateSourceKind.IMMICH,
            date=immich_dt,
            file_path=asset_wrapper.asset.original_path,
            asset=asset_wrapper.asset,
        )

    # WhatsApp filename date
    filename = asset_wrapper.asset.original_file_name
    wa_filename_dt = extract_whatsapp_date_from_path(filename)
    wa_filename_candidate = None
    if wa_filename_dt:
        wa_filename_candidate = AssetDateCandidate(
            source_kind=DateSourceKind.WHATSAPP_FILENAME,
            date=wa_filename_dt,
            file_path=filename,
            asset=asset_wrapper.asset,
        )

    # WhatsApp path date
    path = asset_wrapper.asset.original_path
    wa_path_dt = extract_whatsapp_date_from_path(path)
    wa_path_candidate = None
    if wa_path_dt:
        wa_path_candidate = AssetDateCandidate(
            source_kind=DateSourceKind.WHATSAPP_PATH,
            date=wa_path_dt,
            file_path=path,
            asset=asset_wrapper.asset,
        )

    return AssetDateSources(
        asset_id=asset_wrapper.asset.id,
        immich_date=immich_candidate,
        whatsapp_filename_date=wa_filename_candidate,
        whatsapp_path_date=wa_path_candidate,
    )
