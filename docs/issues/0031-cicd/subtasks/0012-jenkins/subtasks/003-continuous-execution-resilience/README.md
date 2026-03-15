# Subtask 003 (Proposed) · Jenkins Continuous Execution / Auto-Relaunch

## Context

Current objective: process as many assets as possible.
Today, runs may stop early (error, timeout, unexpected termination), leaving pending assets.

This document defines a **proposal** (not implemented yet) to keep Jenkins relaunching the processing job after completion/failure.

## Goal

Guarantee near-continuous processing by relaunching the job when it finishes, while avoiding infinite branch storms in a multibranch setup.

## Key constraint: Multibranch behavior

In a Jenkins Multibranch Pipeline, putting auto-relaunch logic directly in `Jenkinsfile` affects **all branches** that execute that file.
Without safeguards, each branch could self-loop.

## Options analyzed

### Option A — Self-relaunch in the same pipeline (fastest)

Add a `post { always { ... } }` block that triggers the same job again:

```groovy
post {
  always {
    script {
      if (env.BRANCH_NAME == 'ops/continuous-processing') {
        build job: env.JOB_NAME, wait: false, propagate: false
      }
    }
  }
}
```

#### Pros
- Very simple.
- Immediate relaunch after success/failure/abort.

#### Risks
- Dangerous in multibranch if not restricted by branch.
- Easy to create loops across many branches.

---

### Option B — Dedicated orchestrator job (recommended)

Create a **separate Jenkins job** (or pipeline) that repeatedly triggers a single target branch/job.
The multibranch pipeline keeps normal behavior; the orchestrator handles the loop.

#### Pros
- Better control and visibility.
- No accidental self-loop on every branch.
- Easier pause/disable without touching product pipeline.

#### Risks
- Slightly more setup.

---

### Option C — Periodic trigger + retries (safer but not immediate)

Use scheduled trigger (`cron`) + retries/timeouts.
Job restarts periodically instead of immediately.

#### Pros
- Lower risk of runaway loop.
- Operationally simpler to throttle.

#### Risks
- Not truly immediate after finish.

## Branch scope recommendation

For your current multibranch model, use **one dedicated branch** for continuous processing, e.g. `ops/continuous-processing`.

- Continuous loop only on that branch.
- Other branches keep CI behavior only (build/check/test).

## Minimum safeguards (must-have)

1. `disableConcurrentBuilds()` to prevent overlap.
2. `timeout(...)` on long stages.
3. Retry policy (`retry(n)`) in critical stages.
4. Branch guard (`if (env.BRANCH_NAME == '...')`).
5. Kill switch flag (env var) to stop relaunch quickly.
6. Build retention to avoid unlimited history growth.

## Suggested next step (discussion)

Decide first:

1. **Scope:** only `ops/continuous-processing` branch or another branch name.
2. **Mechanism:** Option A (in-pipeline) vs Option B (orchestrator, recommended).
3. **Safety limits:** max retries, timeout, and whether relaunch should also happen on `aborted`.

Once decided, implementation can be prepared as a small controlled change in `Jenkinsfile` (or orchestrator pipeline), with explicit guardrails.

---

## Option B in practice (what is Jenkins UI vs repo code)

### What is configured in Jenkins UI

1. Create a new Jenkins job of type **Pipeline**.
2. Name it, for example: `immich-autotag-continuous-orchestrator`.
3. In Pipeline definition, choose one of:
  - **Pipeline script from SCM** (recommended for versioning), or
  - **Pipeline script** (paste directly in Jenkins UI).
4. Use the script provided in:
  - `orchestrator_pipeline.groovy`

### What is modified in repository code

- For Option B minimum viable setup: **nothing is required** in product `Jenkinsfile`.
- Optional hardening in product pipeline is still recommended (`disableConcurrentBuilds`, stage timeouts).

---

## Step-by-step setup (recommended)

1. Create branch dedicated to continuous execution (example):
  - `ops/continuous-processing`
2. Ensure multibranch job discovers that branch.
3. Open target branch job page in Jenkins and copy **Full project name**.
4. Configure orchestrator parameter `TARGET_JOB` with that full name.
5. Start with conservative values:
  - `MAX_CYCLES=0` (infinite)
  - `MAX_CONSECUTIVE_FAILURES=12`
  - `SLEEP_SECONDS_SUCCESS=20`
  - `SLEEP_SECONDS_FAILURE=60`
  - `STOP_ON_ABORTED=true`
6. Run orchestrator manually first and observe 2–3 cycles.

---

## Operational controls

- **Stop safely:** run job with `LOOP_ENABLED=false`.
- **Pause behavior after failures:** tune `SLEEP_SECONDS_FAILURE`.
- **Prevent infinite error storms:** keep `MAX_CONSECUTIVE_FAILURES` finite.
- **Do not target all branches:** point `TARGET_JOB` to one dedicated branch job.

---

## Included assets in this folder

- `README.md` (this document)
- `orchestrator_pipeline.groovy` (production-safe orchestrator reference)
