# get_asset_date_sources.py
# Función: get_asset_date_sources
from immich_autotag.assets.asset_response_wrapper import AssetResponseWrapper

from immich_autotag.assets.date_correction.extract_whatsapp_date_from_path import extract_whatsapp_date_from_path
from immich_autotag.assets.date_correction.asset_date_candidate import AssetDateCandidate
from immich_autotag.assets.date_correction.asset_date_candidates import AssetDateCandidates
from immich_autotag.assets.date_correction.date_source_kind import DateSourceKind



def get_asset_date_candidates(asset_wrapper: AssetResponseWrapper) -> AssetDateCandidates:
    """
    Extract all relevant date candidates for a given asset.
    Returns an AssetDateCandidates object with all found AssetDateCandidate objects.
    """
    candidates = AssetDateCandidates()
    # IMMICH date
    immich_dt = asset_wrapper.get_best_date()
    if immich_dt:
        candidates.add(AssetDateCandidate(
            source_kind=DateSourceKind.IMMICH,
            date=immich_dt,
            file_path=asset_wrapper.asset.original_path,
            asset=asset_wrapper.asset,
        ))

    # WhatsApp filename date
    filename = asset_wrapper.asset.original_file_name
    wa_filename_dt = extract_whatsapp_date_from_path(filename)
    if wa_filename_dt:
        candidates.add(AssetDateCandidate(
            source_kind=DateSourceKind.WHATSAPP_FILENAME,
            date=wa_filename_dt,
            file_path=filename,
            asset=asset_wrapper.asset,
        ))

    # WhatsApp path date
    path = asset_wrapper.asset.original_path
    wa_path_dt = extract_whatsapp_date_from_path(path)
    if wa_path_dt:
        candidates.add(AssetDateCandidate(
            source_kind=DateSourceKind.WHATSAPP_PATH,
            date=wa_path_dt,
            file_path=path,
            asset=asset_wrapper.asset,
        ))

    # TODO: Add other filename/date extraction logic as needed

    return candidates
