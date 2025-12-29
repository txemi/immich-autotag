# get_asset_date_sources.py
# Función: get_asset_date_sources
from immich_autotag.assets.asset_response_wrapper import AssetResponseWrapper
from immich_autotag.assets.date_correction.asset_date_sources import AssetDateSources
from immich_autotag.assets.date_correction.extract_whatsapp_date_from_path import (
    extract_whatsapp_date_from_path,
)


def get_asset_date_sources(asset_wrapper: AssetResponseWrapper) -> AssetDateSources:
    """
    Extract all relevant date sources for a given asset.
    Returns an AssetDateSources object with immich_date, WhatsApp filename date, and WhatsApp path date.
    """
    immich_date = asset_wrapper.get_best_date()
    wa_filename_date = extract_whatsapp_date_from_path(
        getattr(asset_wrapper.asset, "original_file_name", "")
    )
    wa_path_date = extract_whatsapp_date_from_path(
        getattr(asset_wrapper.asset, "original_path", "")
    )
    return AssetDateSources(
        asset_id=asset_wrapper.asset.id,
        immich_date=immich_date,
        whatsapp_filename_date=wa_filename_date,
        whatsapp_path_date=wa_path_date,
    )
