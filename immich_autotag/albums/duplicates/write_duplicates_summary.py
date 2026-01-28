import json

from typeguard import typechecked

from immich_autotag.albums.duplicates.duplicate_album_reports import (
    DuplicateAlbumReports,
)
from immich_autotag.run_output.manager import RunOutputManager


@typechecked
def write_duplicates_summary(_collected_duplicates: DuplicateAlbumReports) -> None:
    """Write collected duplicates to `run_output_dir/albums_duplicates_summary.json` (best-effort)."""
    try:
        run_exec = RunOutputManager.get_run_output_dir()
        out_file = run_exec.get_albums_duplicates_summary_path()
        out_file.parent.mkdir(parents=True, exist_ok=True)
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
