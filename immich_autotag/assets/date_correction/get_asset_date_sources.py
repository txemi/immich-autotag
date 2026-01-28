# get_asset_date_sources.py
# Function: get_asset_date_sources
from pathlib import Path

from immich_autotag.assets.asset_response_wrapper import AssetResponseWrapper
from immich_autotag.assets.date_correction.asset_date_candidate import (
    AssetDateCandidate,
)
from immich_autotag.assets.date_correction.asset_date_candidates import (
    AssetDateCandidates,
)
from immich_autotag.assets.date_correction.date_source_kind import DateSourceKind
from immich_autotag.assets.date_correction.extract_whatsapp_date_from_path import (
    extract_whatsapp_date_from_path,
)


def get_asset_date_candidates(
    asset_wrapper: AssetResponseWrapper,
) -> AssetDateCandidates:
    """
    Extract all relevant date candidates for a given asset.
    Returns an AssetDateCandidates object with all found AssetDateCandidate objects.
    """
    candidates = AssetDateCandidates(asset_wrapper=asset_wrapper)
    # IMMICH date
    immich_dt = asset_wrapper.get_best_date()
    if immich_dt:
        candidates.add(
            AssetDateCandidate.from_internal_attrs(
                source_kind=DateSourceKind.IMMICH,
                date=immich_dt,
                file_path=Path(asset_wrapper.get_original_path()),
                asset_wrapper=asset_wrapper,
            )
        )

    # WhatsApp filename date
    filename = asset_wrapper.get_original_file_name()
    wa_filename_dt = extract_whatsapp_date_from_path(str(filename))
    if wa_filename_dt:
        candidates.add(
            AssetDateCandidate.from_internal_attrs(
                source_kind=DateSourceKind.WHATSAPP_FILENAME,
                date=wa_filename_dt,
                file_path=Path(filename),
                asset_wrapper=asset_wrapper,
            )
        )

    # WhatsApp path date
    path = asset_wrapper.get_original_path()
    wa_path_dt = extract_whatsapp_date_from_path(str(path))
    if wa_path_dt:
        candidates.add(
            AssetDateCandidate.from_internal_attrs(
                source_kind=DateSourceKind.WHATSAPP_PATH,
                date=wa_path_dt,
                file_path=Path(path),
                asset_wrapper=asset_wrapper,
            )
        )

    # Detect dates in camera-style filenames (FILENAME)
    from immich_autotag.assets.date_correction.extract_date_from_filename import (
        extract_date_from_filename,
    )

    filename_date = extract_date_from_filename(str(filename))
    if filename_date:
        candidates.add(
            AssetDateCandidate.from_internal_attrs(
                source_kind=DateSourceKind.FILENAME,
                date=filename_date,
                file_path=Path(filename),
                asset_wrapper=asset_wrapper,
            )
        )

    return candidates
