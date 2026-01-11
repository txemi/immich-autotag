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

## Safe Cleanup Strategy

To avoid leaving public repositories empty and ensure users always have access to a valid and controlled version, follow this procedure:

1. **Select a new and high version number (e.g., 0.48.0)**
   - This clearly marks the "safe point" for cleanup and leaves room for intermediate versions if needed.

2. **Run the full release with version 0.48.0**
   - Publish to PyPI, TestPyPI, and Docker Hub.
   - Verify that version 0.48.0 is available and accessible in all registries.

3. **Manually delete all previous versions/tags before 0.48.0**
   - Use the links in `manual_cleanup_links.md` to delete everything except 0.48.0.
   - This ensures users can only install/pull the latest and safest version.

4. **(Optional) Run a new release with an even newer version (e.g., 0.50.0)**
   - This allows the cleanup to be "historical" and development to continue with a clearly later version.

5. **Document in the issue that version 0.48.0 (or the chosen one) is the safe point after cleanup.**

## Safe Cleanup Status Update (Jan 11, 2026)

- The latest release published is **version 0.54.0**, which has been verified to deploy cleanly to PyPI, TestPyPI, and Docker Hub.
- All previous versions/tags have been manually deleted from all public registries, leaving only 0.54.0 as the clean baseline.
- The release process now uses explicit version numbers, and all review links and Docker tags are correct.
- The workspace and public registries are now fully clean and ready for future releases, with no legacy or "garbage" versions remaining.

---

*Version 0.54.0 is now the sole published version. The cleanup is complete and the project is ready for new deployments.*

## Preliminary step: New release to restore generic tags

**Motivation:**
During the cleanup, all versions and generic tags (such as `latest`, `cron`, etc.) were removed, which may cause failures in execution and deployment scripts that depend on them.

**Action:**
- Perform a new release (for example, 0.56.0) using the usual deployment script.
- Verify that all necessary generic tags are regenerated and point to the new version.
- Confirm that execution and deployment scripts work correctly with the restored tags.

**Expected result:**
Generic tags will be up to date and users will be able to execute and deploy without issues.

---

## Next step: Validation on a different machine

**Objective:**
Ensure that execution and deployment scripts work correctly on a different machine, without hidden local dependencies.

**Procedure:**
1. Clone the repository on the new machine.
2. Install the necessary dependencies (Python, Docker, etc.).
3. Run the deployment and execution scripts (not image creation scripts).
4. Verify that the application runs correctly and deployments work as expected.
5. Document any issues or differences found.

**Expected result:**
The process should be reproducible and work correctly in any clean environment, confirming the robustness of the deployment system.
