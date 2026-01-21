# tee_logging.py
#
# Utility to duplicate stdout and stderr to a file in real time,
# without memory buffers.


import sys

from typeguard import typechecked


class Tee:
    def __init__(self, filename: str, mode: str = "a"):
        # Open the file with buffering=1 (line buffered) to ensure real-time logging
        self.file = open(filename, mode, buffering=1, encoding="utf-8")
        self.stdout = sys.stdout
        self.stderr = sys.stderr
        # Redirect global streams
        sys.stdout = self
        sys.stderr = self

    def __del__(self):
        self.close()

    def write(self, data):
        # Filter out extremely large DTO reprs that flood the logs.
        # If a known DTO pattern appears in the output, replace it with a short placeholder.
        try:
            if isinstance(data, str) and data:
                banned_markers = (
                    "AssetResponseDto(",
                    "ExifResponseDto(",
                    "AlbumResponseDto(",
                    "DuplicateResponseDto(",
                )
                for marker in banned_markers:
                    if marker in data:
                        # Replace the large representation with a concise marker.
                        data = data.replace(marker, "[DTO_TRUNCATED:(")
                        # Additionally, if the line is extremely long, truncate it to a safe size
                        MAX_LEN = 1000
                        if len(data) > MAX_LEN:
                            data = data[:MAX_LEN] + "... [TRUNCATED]\n"
                        break
        except Exception:
            # Don't let filtering break logging; fall back to original data
            pass

        self.stdout.write(data)
        self.file.write(data)
        self.file.flush()
        self.stdout.flush()

    def flush(self):
        self.stdout.flush()
        self.file.flush()

    def close(self):
        if sys.stdout is self:
            sys.stdout = self.stdout
        if sys.stderr is self:
            self.stderr = self.stderr
        if not self.file.closed:
            self.file.close()


@typechecked
def setup_tee_logging(basename: str = "immich_autotag_full_output.log") -> None:
    """
    Duplicates stdout and stderr to a file in real time, without memory buffers.
    The file is created in the current run's log directory
    (get_run_output_dir()), and the base name can be customized.
    """
    from immich_autotag.utils.run_output_dir import get_run_output_dir

    log_dir = get_run_output_dir()
    log_path = log_dir / basename
    Tee(str(log_path), "a")
