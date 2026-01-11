# User Simulation: Immich AutoTag Deployment and Execution Tests

## Context

We are simulating the experience of a new user on a fresh machine, following the official documentation to deploy and run Immich AutoTag. The goal is to validate all documented execution methods and detect any issues, outdated references, or missing steps.

## Source of Test Scenarios

All main user-facing execution options are described in the project `README.md`. Additional useful scripts may exist in the repository, but the README is considered the canonical source for end-user instructions.

## Planned Tests

### 1. Docker-based Execution

#### 1.1. One-shot execution (public image)
- Command: `bash scripts/docker/run_docker_public.sh`
- Expected: Runs the latest public image from Docker Hub (`txemi/immich-autotag:latest`).

#### 1.2. One-shot execution (local image)
- Command: `bash scripts/docker/run_docker_with_config.sh`
- Expected: Runs the local image (`immich-autotag:latest`).
- Option: `bash scripts/docker/run_docker_with_config.sh --image txemi/immich-autotag:latest` (forces public image).

#### 1.3. Periodic execution (cron mode)
- Command: `docker run -d --name autotag-cron -e CRON_SCHEDULE="0 2 * * *" -v ~/.config/immich_autotag:/root/.config/immich_autotag txemi/immich-autotag:cron`
- Variants: Change schedule, map log volume, etc.

#### 1.4. Periodic execution with Docker Compose
- Command: `docker compose up -d` (using provided `docker-compose.yml`)
- Expected: Manages cron service and volumes, logs available in `docker_logs`.

### 2. pipx-based Execution
- Command: `pipx run immich-autotag`
- Expected: Runs the tool without code download.

### 3. Direct Script Execution (from repo)
- Command: `./scripts/run_immich_autotag.sh`
- Expected: Runs the tool using local code.

### 4. Additional/Advanced User Scripts
- Review any other scripts in `scripts/` that may be useful for end users (e.g., continuous tagging loop, statistics, etc.).
- Document if relevant for user-facing workflows.

## Next Steps
- For each test, record the command, expected behavior, and actual result (including any errors or issues).
- Update this document with findings and recommendations for documentation improvements.

---

*This document will serve as a checklist and log for user simulation and validation of all documented execution methods.*
