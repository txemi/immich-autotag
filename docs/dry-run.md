---
uuid: a8d4fa73-b1a5-430a-ac9a-623a3601e235
---

# 1. Dry-run mode

A dry run goes through the whole pipeline as a normal pass does (classification,
temporary `<date>-autotag-temp-unclassified` albums, tags, date fixes, conversions,
album dates, permissions), but **writes nothing to Immich**. Every change it would make
is recorded instead, so you can measure a run before launching it for real: how many
assets would go into temporary albums, how many dates would change, and so on.

## 1.1. How to run it

```bash
python -m immich_autotag --dry-run
# or
bash run_app.sh --dry-run
# or, where passing flags is awkward (cron, Docker):
IMMICH_AUTOTAG_DRY_RUN=1 python -m immich_autotag
```

`IMMICH_AUTOTAG_DRY_RUN` accepts `1`, `true`, `yes`, `on` (and `0`, `false`, `no`, `off`,
or empty, for a normal run). Any other value stops the run with an error. A command-line
argument that looks like a misspelt dry-run flag (`--dryrun`, `--dry_run`...) also stops
the run: ignoring it would run for real what was meant as a test.

**Docker.** The cron image (`Dockerfile.cron`) starts the job from cron, which does not see
the container's environment; its entrypoint copies `IMMICH_AUTOTAG_DRY_RUN` into the
crontab, so `docker run -e IMMICH_AUTOTAG_DRY_RUN=1 …` is a dry run there too. Both images
install `immich-autotag` from PyPI: a release older than this mode ignores the variable and
the flag, and runs **for real**. Before launching, check that the installed release has
the mode: `python -c "import immich_autotag.dry_run"` fails on one without it. Afterwards,
a dry run always leaves `logs_local/dry_run/` (section 1.2).

## 1.2. What it leaves

The run folder of a dry run lives apart, under `logs_local/dry_run/<date>_PID<pid>/`:

| File | Content |
|---|---|
| `dry_run_changes.jsonl` | One JSON line per write that was **not** sent: operation, method, path, target (album id and name, whether it is a temporary album, old and new date...), asset ids, request body, the simulated answer. Written as it happens, so an interrupted run keeps what it saw. |
| `dry_run_summary.json` | The counts: writes intercepted, reads sent, calls and assets per operation, temporary albums (created, assets added, distinct assets, removals), asset dates (updates, distinct assets), simulated ids, writes with no simulation, and the counts of the usual modification report. Written at the end, also when the run fails (`"completed": false`). |

The summary is also printed at the end of the run. The usual outputs (logs, modification
report, statistics) are still written in the same folder.

A dry run is isolated from other runs: it neither reuses the caches and checkpoints of
earlier runs nor leaves any for later ones (they hold simulated state), and real runs
never look into `logs_local/dry_run/`. So a dry run always starts from the current state
of the library; it does not resume from a previous checkpoint.

## 1.3. How it works

The writes are cut in **one place**: the HTTP transport of the Immich client
(`immich_autotag/dry_run/dry_run_transport.py`), installed by `ImmichClientWrapper` when
the mode is on. Every call to Immich goes through that client, so no write can leave the
process even from a code path that knows nothing about the dry run.

- **Reads** are sent to Immich: `GET`, `HEAD`, `OPTIONS`, and every `POST` under
  `/search/` (Immich searches with `POST /search/metadata`, `/search/smart`...).
- **Everything else is a write** and is never sent, including endpoints nobody listed.
  The known writes (album create, rename, delete, add and remove assets, album users,
  asset update, tag create, delete, tag and untag assets) are answered as Immich would
  answer them. An unknown write is answered with an error (HTTP 501) and recorded.
- **Coherence:** when the pipeline needs the result of a write to go on, the dry run
  simulates it. A new album or tag gets a simulated id (`00000000-d7d7-4000-8000-…`),
  listed in the summary; reads about it are answered by the simulation and never reach
  Immich. Reads that Immich answers are patched with the simulated changes: the album
  list shows the new albums, an album search shows the assets that were "added", an
  asset shows its new date and tags.

## 1.4. Limits

- Album fields that only Immich computes (album start and end dates, thumbnails) are not
  recalculated for simulated changes.
- Searches are patched only when they filter by a single album or tag; a search on
  several at once shows the library as it is on the server.
- The counts are those of one pass: if a real run would need several passes to settle,
  the dry run shows only the first.
