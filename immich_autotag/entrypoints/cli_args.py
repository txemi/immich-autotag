"""
Command-line options of immich-autotag.

Until now the command line was ignored (the Docker image even passes ``--help``
and still runs a normal pass), so only the options below are read, and other
arguments keep being ignored with a warning. The one exception is an argument
that looks like a misspelt dry-run option (``--dryrun``, ``--dry_run``...): that
stops the run, because ignoring it would run for real what was meant as a test.
"""

from __future__ import annotations

import argparse

DRY_RUN_FLAG = "--dry-run"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="immich-autotag",
        add_help=False,
        description="Rule engine that applies batch changes to an Immich library.",
    )
    parser.add_argument(
        DRY_RUN_FLAG,
        action="store_true",
        help=(
            "Run the whole pipeline without writing anything to Immich. Each change "
            "that would be made is written to dry_run_changes.jsonl, and the counts "
            "to dry_run_summary.json, in the run folder under logs_local/dry_run/. "
            "Same as IMMICH_AUTOTAG_DRY_RUN=1."
        ),
    )
    return parser


def _looks_like_dry_run(argument: str) -> bool:
    normalized = argument.lower().lstrip("-").replace("_", "").replace("-", "")
    return normalized.startswith("dry")


def parse_cli_args(argv: list[str]) -> argparse.Namespace:
    """Parses the known options; raises SystemExit on a misspelt dry-run option."""
    parser = build_parser()
    args, unknown = parser.parse_known_args(argv)
    misspelt = [a for a in unknown if _looks_like_dry_run(a)]
    if misspelt:
        parser.error(
            f"unrecognised option(s) {misspelt}: did you mean {DRY_RUN_FLAG}? "
            "Refusing to run for real."
        )
    if unknown:
        print(f"[WARNING] Ignoring command-line arguments: {unknown}")
    return args


def apply_cli_args(argv: list[str]) -> argparse.Namespace:
    """Parses the command line and switches on what it asks for."""
    args = parse_cli_args(argv)
    if args.dry_run:
        from immich_autotag.dry_run.dry_run_mode import activate_dry_run

        activate_dry_run()
        print(
            "[DRY-RUN] Dry-run mode: nothing will be written to Immich; "
            "the changes that would be made are recorded instead."
        )
    return args
