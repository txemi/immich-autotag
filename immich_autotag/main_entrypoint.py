def run_main():
    import sys

    # The command line is read before anything else is imported: the dry-run
    # switch decides where the run folder goes and which HTTP transport the
    # Immich client gets, and both are fixed when the main module is imported.
    from immich_autotag.entrypoints.cli_args import apply_cli_args

    apply_cli_args(sys.argv[1:])

    from immich_autotag.entrypoints.main_entrypoint import run_main

    return run_main()
