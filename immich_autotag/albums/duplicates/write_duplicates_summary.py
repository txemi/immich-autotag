import json

from typeguard import typechecked

from immich_autotag.albums.duplicates.duplicate_album_reports import (
    DuplicateAlbumReports,
)
from immich_autotag.utils.run_output_dir import get_run_output_dir


@typechecked
def write_duplicates_summary(_collected_duplicates: DuplicateAlbumReports) -> None:
    """Write collected duplicates to `run_output_dir/albums_duplicates_summary.json` (best-effort)."""
    try:
        out_dir = get_run_output_dir()
        out_dir.mkdir(parents=True, exist_ok=True)
        out_file = out_dir / "albums_duplicates_summary.json"
        duplicates_list = _collected_duplicates.to_list()
        with out_file.open("w", encoding="utf-8") as fh:
            json.dump(
                {"count": len(duplicates_list), "duplicates": duplicates_list},
                fh,
                indent=2,
            )
    except Exception:
        # Best-effort
        pass
