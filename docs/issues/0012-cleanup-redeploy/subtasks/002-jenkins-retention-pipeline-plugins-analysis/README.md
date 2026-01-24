# Jenkins: Build/Workspace Retention and Cleanup via Pipeline and Plugins

## Context

This analysis and actions are independent from the previous sub-task (Groovy Script) and document the current state and options for sustainable, automatic space management in Jenkins, focusing on declarative pipelines and plugins, not ad-hoc scripts.

---

## Actions performed (January 2026)

- The Jenkinsfile was updated to include a build retention policy:
  ```groovy
  options {
      buildDiscarder(logRotator(numToKeepStr: '4'))
  }
  ```
  This ensures Jenkins will only keep the last 4 builds for each branch/pipeline.

- The retention mechanism in Jenkins was analyzed:
  - **The policy in the Jenkinsfile takes precedence** over the multibranch job UI configuration.
  - If there is no policy in the Jenkinsfile, the UI configuration is used.
  - There is no global option to clean builds for all jobs at once (except via Groovy scripts or advanced plugins).

---

## Sustainable options for automatic cleanup

1. **Build and artifact retention**
   - `buildDiscarder` in the Jenkinsfile controls how many builds and artifacts are kept.
   - Advanced example:
     ```groovy
     options {
         buildDiscarder(logRotator(numToKeepStr: '4', artifactNumToKeepStr: '2'))
     }
     ```

2. **Workspace cleanup after each build**
   - Requires the Workspace Cleanup plugin.
   - Add to the Jenkinsfile:
     ```groovy
     post {
         always {
             cleanWs()
         }
     }
     ```

3. **Useful plugins**
   - **Workspace Cleanup Plugin:** Cleans the workspace after each build.
   - **Artifact Cleanup Plugin:** Deletes old artifacts without deleting the build record.
   - **Orphaned Item Strategy Plugin:** Automatically cleans up orphaned jobs in multibranch (configurable only from the UI).

4. **Groovy scripts**
   - For global or advanced cleanup, a Groovy script can be used in the Script Console (see previous sub-task).

---

## Current state
- Jenkinsfile updated with build retention policy.
- Plugins analyzed and ready to install/configure if more aggressive cleanup is needed.
- Previous sub-task and scripts were not modified.

---

## Suggested next steps
- Install and test Workspace Cleanup Plugin and/or Artifact Cleanup Plugin if more cleanup is required.
- Periodically review disk usage and adjust policies as needed.
- Document any further changes in this sub-task.
