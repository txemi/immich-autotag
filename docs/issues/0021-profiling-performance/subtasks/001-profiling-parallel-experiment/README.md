# Subtask 001 — Parallel profiling experiment

Purpose
- Document and execute a controlled experiment to understand why the test suite execution time has grown (e.g. 4 h → 14–15 h).
- Have an organized space to save snapshots (logs, pstats profiles, outputs from `run_app.sh`) captured at key moments and facilitate their comparative analysis.

Summary of proposed experiment
1. Run a first job (Job A) with profiling enabled.
2. Wait ~1 hour from the start to collect a snapshot (logs, estimate/processed counters, profile.stats, system metrics).
3. Launch a second job (Job B) **in parallel** with Job A.
4. Wait another hour and collect a second snapshot (for Job A and for Job B), compare estimates and profiles.
5. Repeat if necessary or extend windows if the numbers are noisy.

Motivation and reasoning
- The estimates shown by the application ("% processed / Avg / Elapsed / Est. remaining") may stabilize after an initial time; taking a single measurement at the start can be misleading.
- By comparing a single execution vs. two parallel executions we can detect:
  - If the degradation is due to interference/resources (CPU, I/O, DB/API contention).
  - If there is degradation due to accumulation of artifacts (e.g. massive album creation) that only becomes visible after a certain % of processing.

Folder structure (template)
- `docs/issues/0021-profiling-performance/subtasks/001-profiling-parallel-experiment/`
  - `README.md` (this file)
  - `snapshots/` (subfolder where local files that you share or reference are stored)
    - `jobA_t0_log.txt` — complete log of Job A execution at the first snapshot (text)
    - `jobA_t0_profile.stats` — pstats (cProfile) generated up to t0
    - `jobA_t0_sys.txt` — output of system commands at t0 (`top -b -n1`, `vmstat 1 5`, `iostat -x 1 5` if available)
    - `jobA_t1_log.txt`, `jobA_t1_profile.stats`, `jobA_t1_sys.txt` — second snapshot
    - `jobB_t0_log.txt`, `jobB_t0_profile.stats`, `jobB_t0_sys.txt` — (if applicable)
    - `notes.md` — manual observations (start time, branch, commit, Jenkins node, machine load)
  - `analysis/` (will be added when analysis is produced)
    - `report.md` — report with executive summary, comparison and recommendations

Minimum snapshot format
- Logs: complete text file; if they are too large, trim but keep the sections:
  - Header with commit SHA, branch and time
  - Progress lines ("[PERF] 76255/270798 ...")
  - Complete tracebacks if they appear
- Profile: `profile.stats` (pstats file from cProfile). If you use py-spy or flamegraph, save `pyspy.svg`/`flamegraph.svg` as well.
- System: text with `top -b -n1`, `vmstat 1 5`, `free -h`, `df -h`, and `iostat -x 1 5` if available.

Useful commands for capturing (examples)
- Generate pstats from `run_app.sh` if `profile_run.sh` is already used (already implemented in repo): the script should produce `profile.stats` in `logs_local/profiling/<TIMESTAMP>/`.
- Commands for system snapshot (from the machine where Jenkins/worker runs):
```bash
# basic snapshot
top -b -n1 > jobA_t0_top.txt
vmstat 1 5 > jobA_t0_vmstat.txt
free -h > jobA_t0_free.txt
uptime >> jobA_t0_uptime.txt
```
- Extract progress/estimate lines from log (example):
```bash
grep '^\[PERF\]' logs_local/.../immich_autotag_full_output.log > jobA_t0_perf_lines.txt
```

Metadata template (add in `notes.md`)
- `job`: JobA / JobB
- `start_time_utc`:
- `snapshot_time_utc`:
- `branch` / `commit`:
- `jenkins_node`:
- `profile_file`:
- `estimate_at_snapshot` (exact line from the log):
- `processed_count_at_snapshot`:
- `total_assets`:
- `concurrent_jobs_on_node` (if you know it):

Privacy / sensitivity
- If logs contain PII or private URLs, do not upload complete files. Instead:
  - Redact `user ids`, `email addresses`, `asset URLs` — replace them with tokens `USER_123`.
  - Keep progress lines, estimates and tracebacks intact.
- Alternative: upload files to a private channel (S3/private drive) and share the paths/IDs with me. Here I will leave references to the file names that you should copy there.

Experiment success criteria
- We will obtain comparable profiles (pstats) and system metrics at two moments (t0, t1) for Job A and, if applicable, Job B.
- The analysis should answer questions like:
  - Is the estimate degradation confirmed between t0 and t1? (how much the relative and absolute ETA changes)
  - Do hotspots appear in the profile that explain the higher CPU per asset?
  - Is contention observed in I/O, swap or CPU due to concurrency?

Proposed operational process (concrete steps)
1. I document this plan (done) and prepare the template folder.
2. You run Job A normally and, after ~1 hour, you pass me (or upload) the files indicated in `snapshots/jobA_t0_*` and the `notes.md` with metadata.
3. Start Job B in parallel.
4. After ~1 more hour, collect `jobA_t1_*` and `jobB_t1_*` (or those that apply) and pass them to me.
5. I analyze the pstats and logs, produce `analysis/report.md` with findings and recommendations.

Quick technical suggestions
- If the size of `profile.stats` is large, compress it (`gzip`) before sharing.
- If you cannot generate pstats, at least capture the progress logs and `top`/`vmstat` at the indicated moments.

Quick checklist for when you prepare snapshot (copy in `notes.md`)
- [ ] UTC time of snapshot
- [ ] Commit / branch being executed
- [ ] Files generated: listed (log, pstats, top, vmstat)
- [ ] Redactions made (if there was PII)
- [ ] Jenkins node / machine identifier

Contact and next steps
- When you have the first snapshot (t0) upload it or tell me where it is and I will analyze it. If you prefer that I wait for t1 to receive both, tell me and I'll wait.

---

If you agree with this plan, confirm it and I will create the structure in the repo (this folder has already been created locally); then tell me how you are going to share the files (directly in the repo, private S3, or other means) and the approximate schedule (UTC time) for the first capture and I will be ready to analyze.
