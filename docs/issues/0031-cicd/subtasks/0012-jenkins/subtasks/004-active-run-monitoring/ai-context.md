# Active Run Monitoring — ai-context

**Last verified:** 2026-04-25

## What we are tracking

Branch `fix/conversion-album-move` is being executed repeatedly by Jenkins.
Each run should:
- Process exactly `max_assets = 30 000` assets
- Resume from the checkpoint left by the previous run (`resume_previous = true`, overlap = 100)
- Push a `jenkins-success-<N>-<sha>` git tag to GitHub on success

The goal is to advance through the full asset library in increments of 30 000 until
all assets have been processed at least once.

## How to verify a run is healthy

From the console log, look for:
- `[PERF]` lines: `Processed:<session_count>/...` — session_count should grow from ~0 to ~30 000
- `Skip:<N>` — N should match the `count` from the previous run minus the overlap (100)
- `Remaining:` — should be positive and decreasing (negative = bug, see fix below)
- Final line: `Total assets processed: 30000`
- A `jenkins-success-*` tag pushed to the GitHub repo

## Fixes applied in this session (2026-04-25)

### fix(perf): negative remaining time with skip_n
- **File:** `immich_autotag/statistics/statistics_manager.py`
- **Commit:** `95daca3f`
- **Root cause:** `run_stats.count` stores `skip_n + session_count` (correct for
  checkpoint resume), but `PerformanceTracker` expected only `session_count`.
  This caused `remaining = total_to_process - abs_count < 0` on every resumed run.
- **Fix:** `_to_session_count()` helper subtracts `skip_n` before handing the value
  to the tracker. All three call sites (`get_progress_description`,
  `maybe_print_progress`, `print_progress`) use it.

### fix(ci): Jenkins GitHub tagging using HTTPS credentials
- **File:** `Jenkinsfile`
- **Commit:** `66a26278`
- **Root cause:** `tagBuild()` used SSH (`git@github.com`) but the Jenkins agent
  running this branch does not have a GitHub SSH deploy key configured.
  Push failed with `Permission denied (publickey)`.
- **Fix:** replaced SSH block with `withCredentials` using the same HTTPS credential
  already used for checkout. No server-side changes required.

## Checkpoint mechanics (how resume works)

See `immich_autotag/statistics/checkpoint_manager.py` and
`immich_autotag/statistics/_find_max_skip_n_recent.py`.

- At the end of each run, `run_stats.count = skip_n + session_count` is saved to YAML.
- The next run reads all recent YAML files, takes the maximum `count`, subtracts an
  overlap of 100, and uses the result as `skip_n`.
- This means runs chain: run 1 ends at ~30 000 → run 2 starts at skip_n ~29 900, etc.

## What to do if a run looks wrong

| Symptom | Likely cause | Where to look |
|---|---|---|
| `Remaining:` is negative | Old code without `95daca3f` | Check deployed version |
| `Skip:0` when it should resume | Checkpoint YAML not found or too old (>3h) | `logs_local/` on the Jenkins agent |
| Tag not pushed | HTTPS credential missing or renamed | Jenkinsfile `credentialsId` |
| `Total assets processed: N` where N < 30 000 | Run was aborted or timed out | Check abort reason in log |
