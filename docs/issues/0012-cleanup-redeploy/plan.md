# Issue 0020: Cleanup and Redeployment Plan for Public Releases

## Context

The project is now public and has users actively testing it. We publish code, helper scripts, Docker containers, and Python libraries to public registries. Recently, we noticed that the Docker Compose setup was not always using the latest published images, and it became unclear which versions were actually deployed or available in public registries. This loss of control can lead to confusion for users and maintainers.

## Objective

Restore full control and traceability over what is published in all public registries (PyPI, TestPyPI, Docker Hub), ensuring that:
- Only the intended, up-to-date versions are available.
- Docker Compose setups always use the latest published images.
- The process is repeatable and documented for future maintenance.

## Plan

- [x] **1. Create a dedicated git branch for the cleanup and redeployment operation.**
   - Name: `chore/cleanup-redeploy-2026-01` (or similar, following project conventions).

- [x] **2. Script: Clean all local Docker images related to the project.**
   - `scripts/docker/clean_local_docker_images.sh` elimina todas las imágenes locales de immich-autotag (one-shot y cron), mostrando el estado antes y después de la limpieza para máxima transparencia.
   - Probado y verificado: elimina todas las imágenes y confirma el resultado.

- [x] **3. Script: Stop Docker Compose services for the project.**
   - `scripts/docker/stop_compose.sh` detiene todos los servicios usando el `docker-compose.yml` de la raíz del proyecto, siguiendo la convención estándar y asegurando máxima compatibilidad.
   - El script detecta la raíz del proyecto y muestra mensajes claros de estado y errores.

- [ ] **4. (Optional) Script: Clean public registries.**
   - If feasible, automate the removal of old images/packages from Docker Hub and PyPI/TestPyPI.
   - If not, document the manual steps required for maintainers.

- [ ] **5. Run the full deployment script.**
   - Use the `full_release.sh` or equivalent to redeploy all images and packages, ensuring everything public is up to date and consistent.

- [x] **6. Document all steps and scripts in this issue folder.**
   - Keep a record of the process, scripts, and any manual interventions for future reference.

## Rationale

- Ensures users always get the latest, intended versions.
- Reduces confusion and support burden.
- Makes the release and maintenance process more robust and auditable.

---

*This issue folder will be updated as the cleanup and redeployment proceeds. All scripts and logs will be included here for traceability.*
