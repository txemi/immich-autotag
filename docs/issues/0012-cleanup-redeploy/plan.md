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
   - `scripts/docker/clean_local_docker_images.sh` removes all local immich-autotag images (one-shot and cron), displaying the status before and after cleanup for maximum transparency.
   - Tested and verified: removes all images and confirms the result.
   - **Status update (2026-01-11):** We have switched to a new machine and are simulating the scenario of an end user following the official documentation. Local Docker images have been cleaned to ensure that all subsequent tests use only recent and public versions. This will help us detect any outdated references or errors in deployment and execution scripts.

- [x] **3. Script: Stop Docker Compose services for the project.**
   - `scripts/docker/stop_compose.sh` stops all services using the root project's `docker-compose.yml`, following the standard convention and ensuring maximum compatibility.
   - The script detects the project root and displays clear status and error messages.

 - [x] **4. (Optional) Script: Clean public registries.**
   - All old images and packages have been removed from Docker Hub and PyPI/TestPyPI, leaving only the latest safe version available. Manual cleanup steps have been documented for maintainers.

 - [x] **5. Run the full deployment script.**
   - The `full_release.sh` (or equivalent) has been run multiple times, redeploying all images and packages up to version 0.54.0 as mentioned in the status update below. All public registries are now up to date and consistent.

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


The latest release published is **version 0.56.0**, which has been verified to deploy cleanly to PyPI, TestPyPI, and Docker Hub.
All previous versions/tags have been manually deleted from all public registries, leaving only 0.56.0 as the clean baseline.
The release process now uses explicit version numbers, and all review links and Docker tags are correct.
The workspace and public registries are now fully clean and ready for future releases, with no legacy or "garbage" versions remaining.

---

*Version 0.56.0 is now the sole published version. The cleanup is complete and the project is ready for new deployments.*

## Preliminary step: New release to restore generic tags

**Motivation:**
During the cleanup, all versions and generic tags (such as `latest`, `cron`, etc.) were removed, which may cause failures in execution and deployment scripts that depend on them.

**Action:**
- Perform a new release (version 0.56.0) using the usual deployment script.
- Verify that all necessary generic tags are regenerated and point to version 0.56.0.
- Confirm that execution and deployment scripts work correctly with the restored tags.

**Expected result:**
Generic tags will be up to date and users will be able to execute and deploy without issues.

---

## Next step: Validation on a different machine


## Next step: Validation on a different machine

**Status update (2026-01-11):**
We have switched to a new machine and are acting as an end user following the official documentation. The first step was to clean all local Docker images to ensure that any test or deployment uses only recent and public versions. Next, we will run the deployment and execution scripts as a new user would, to validate reproducibility and detect possible errors or hidden dependencies.

**Procedure:**
1. Clone the repository on the new machine.
2. Install the necessary dependencies (Python, Docker, etc.).
3. Run the deployment and execution scripts (not the image creation scripts).
4. Verify that the application works correctly and deployments are performed as expected.
5. Document any issues or differences found.

**Expected result:**
The process should be reproducible and work correctly in any clean environment, confirming the robustness of the deployment system.
