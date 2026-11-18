"""
Dry-run mode: run the whole pipeline without writing anything to Immich.

The writes are cut in one place, the HTTP transport of the Immich client
(DryRunTransport). Each change that would be made is recorded in a JSONL file and
counted in a JSON summary. See docs/dry-run.md.
"""
