# 1. User Simulation: Immich AutoTag Deployment and Execution Tests



## 1.1. Context

We are simulating the experience of a new user on a fresh machine, following the official documentation to deploy and run Immich AutoTag. The goal is to validate all documented execution methods and detect any issues, outdated references, or missing steps.

## 1.2. Source of Test Scenarios

All main user-facing execution options are described in the project `README.md`. Additional useful scripts may exist in the repository, but the README is considered the canonical source for end-user instructions.

## 1.3. Environment Cleanup (Pre-Test)

Before running any user simulation tests, we must ensure the environment is clean and free of legacy artifacts. This guarantees that all tests use only the latest public versions and that no local images or caches interfere with reproducibility.

### 1.3.1. Steps Performed

1. **Clean all local Docker images related to Immich AutoTag**
   - Script used: `scripts/docker/clean_local_docker_images.sh`
   - Result: All local images (one-shot and cron) removed. Verified before and after cleanup.

2. **Stop all Docker Compose services for the project**
   - Script used: `scripts/docker/stop_compose.sh`
   - Result: All services stopped, ensuring no running containers interfere with tests.

3. **(Optional) Remove any local build artifacts or caches**
   - If present, clean `dist/`, `.venv/`, or other build folders to avoid accidental use of local code.



### 1.3.2. Clean State Confirmation

All environment cleanup steps have been completed:

- Volúmenes Docker no utilizados eliminados
- Redes Docker no utilizadas eliminadas
- Imágenes y contenedores colgantes eliminados
- Cachés de build y dependencias (Docker y Python) limpiados
- Archivos temporales y artefactos locales borrados

El entorno está listo para iniciar las pruebas de simulación de usuario, garantizando reproducibilidad y ausencia de residuos de ejecuciones previas.
*With the environment fully cleaned, we proceed to user simulation tests below.*

## 1.4. Planned Tests

### 1.4.1. Docker-based Execution

#### 1.4.1.1. One-shot execution (public image)
- Command: `bash scripts/docker/one_shot/run_docker_public.sh`
- Expected: Runs the latest public image from Docker Hub (`txemi/immich-autotag:latest`).

 - Result: ✅ Success. The script automatically detects and mounts the configuration and log directory, fixes output directory permissions before launching the container, and runs the process without manual errors. The system works as expected and the test is reproducible for new users.

#### 1.4.1.2. One-shot execution (local image)
- Command: `bash scripts/docker/run_docker_with_config.sh`
- Expected: Runs the local image (`immich-autotag:latest`).
- Option: `bash scripts/docker/run_docker_with_config.sh --image txemi/immich-autotag:latest` (forces public image).

#### 1.4.1.3. Periodic execution (cron mode)
- Command: `docker run -d --name autotag-cron -e CRON_SCHEDULE="0 2 * * *" -v ~/.config/immich_autotag:/root/.config/immich_autotag txemi/immich-autotag:cron`
- To change the schedule, set the `CRON_SCHEDULE` environment variable (e.g., `-e CRON_SCHEDULE="*/5 * * * *"` for every 5 minutes).
- Variants: Change schedule, map log volume, etc.

#### 1.4.1.4. Periodic execution with Docker Compose
 - Command: `bash scripts/docker/cron/up_compose.sh`
 - Expected: Starts the autotag-cron service using Docker Compose from any directory, manages cron service and volumes, logs available in `docker_logs`.
 - Customizing the schedule: You can change the execution frequency by editing the `CRON_SCHEDULE` environment variable in `docker-compose.yml`.
    - Example (every 5 minutes):
       ```yaml
       environment:
          - CRON_SCHEDULE=*/5 * * * *
       ```
    - By default, it is set to run every day at 2:00 AM (`0 2 * * *`).


### 1.4.2. pipx-based Execution


- Command: `bash scripts/run/run_immich_autotag.sh`
- Expected: Runs the tool using pipx, installing pipx with apt if needed.
- Resultado: ✅ Éxito. El script instala pipx correctamente usando apt en Ubuntu/Debian y ejecuta Immich AutoTag sin problemas. Se recomienda este método para reproducibilidad y facilidad de uso.


### 1.4.3. Additional/Advanced User Scripts
- Review any other scripts in `scripts/` that may be useful for end users (e.g., continuous tagging loop, statistics, etc.).
- Document if relevant for user-facing workflows.

## 1.5. Next Steps
- For each test, record the command, expected behavior, and actual result (including any errors or issues).
- Update this document with findings and recommendations for documentation improvements.

---

*This document will serve as a checklist and log for user simulation and validation of all documented execution methods.*
