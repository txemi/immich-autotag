from pathlib import Path

import attrs


@attrs.define(auto_attribs=True, slots=True, frozen=True)
class RunExecution:
    """
    Encapsulates an execution path (subfolder of logs_local created by an app run).
    Allows access to logs, statistics, caches, etc. for that execution.
    """

    run_dir: Path = attrs.field(converter=Path)

    def get_run_statistics_path(self) -> Path:
        """
        Returns the path to the statistics counters file for this execution.
        Uses the RUN_STATISTICS_FILENAME symbol for traceability.
        """
        from immich_autotag.statistics.constants import RUN_STATISTICS_FILENAME

        return self.get_custom_path(RUN_STATISTICS_FILENAME)

    def get_user_config_dump_path(self) -> Path:
        """
        Returns the path to the user configuration dump file for this execution.
        """
        return self.get_custom_path("user_config_dump.yaml")

    def get_api_cache_dir(self, cache_type: str) -> Path:
        """
        Returns the path to the API cache directory for a given type (e.g. 'albums', 'assets').
        """
        d = self.run_dir / "api_cache" / cache_type
        d.mkdir(parents=True, exist_ok=True)
        return d

    def get_modification_report_path(self) -> Path:
        """
        Returns the path to the modification report file for this execution.
        """
        return self.get_custom_path("modification_report.txt")

    def get_log_path(self, name: str) -> Path:
        return self.run_dir / f"{name}.log"

    def get_stats_path(self, name: str) -> Path:
        return self.run_dir / f"{name}.stats"

    def get_cache_dir(self, name: str) -> Path:
        d = self.run_dir / f"cache_{name}"
        d.mkdir(exist_ok=True)
        return d

    def get_custom_path(self, *parts: str) -> Path:
        p = self.run_dir.joinpath(*parts)
        p.parent.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def path(self) -> Path:
        return self.run_dir

    def __str__(self):
        return str(self.run_dir)

    def __repr__(self):
        return f"<RunExecution {self.run_dir}>"
