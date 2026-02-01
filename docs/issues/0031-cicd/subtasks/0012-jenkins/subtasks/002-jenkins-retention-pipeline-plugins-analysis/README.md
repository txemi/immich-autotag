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

## Groovy Executor Script (jenkins_retention_executor.groovy)

A ready-to-use script implementing both build retention and workspace cleanup is provided in this directory.

### ⭐ THE MAGIC LINK: Jenkins CLI Method (Simplest!)

**The easiest way to run scripts WITHOUT using the Jenkins UI:**

```bash
java -jar jenkins-cli.jar -s http://<jenkins-url> groovy = < jenkins_retention_executor.groovy
```

**Why it's "magical":**
- ✅ One simple command
- ✅ No UI navigation needed
- ✅ Easy to automate/schedule with cron

---

### 🐛 Improvements: Orphaned Workspace Detection

**Problem Addressed:**
In multi-node Jenkins architectures, orphaned workspace directories can accumulate when jobs are deleted or disabled without proper cleanup:
1. **Master vs Agent separation:** Each node maintains its own workspace directory
2. **Path detection:** Scripts must correctly identify active vs orphaned workspaces
3. **Robust deletion:** Handles permission issues and file locking gracefully

**Solution Provided:**
The `jenkins_retention_executor.groovy` script provides:
- Auto-detection of node type (Master/Agent) via JENKINS_HOME environment variable
- Set-based workspace comparison for O(1) orphan detection
- Proper exception handling and progress reporting
- DRY RUN mode for safe preview of cleanup operations
- Build retention policy enforcement

**Architecture Support:**
```
Jenkins MASTER:
  └─ JENKINS_HOME: /var/lib/jenkins/
  └─ Workspace: /var/lib/jenkins/workspace/

Jenkins AGENT:
  └─ JENKINS_HOME: /home/jenkins-agent/ (or custom path)
  └─ Workspace: /home/jenkins-agent/workspace/
```

**Features:**
- ✅ Runs within Jenkins security context
- ✅ No timeout issues (unlike Script Console UI)
- ✅ Can be integrated into maintenance pipelines
- ✅ Works on both Master and Agent nodes
- ✅ Detailed operation logging and reporting

**📚 Official Jenkins CLI Documentation:**
- https://www.jenkins.io/doc/book/managing/cli/
- https://www.jenkins.io/doc/book/managing/groovy-hook-scripts/

---

### Features:
- Keeps N most recent builds per job
- Keeps M most recent builds with artifacts
- Deletes orphaned workspaces
- Dry-run mode for safety (preview before executing)
- Detailed logging and statistics
- Configurable via simple parameters at the top

### Execution Methods

#### Method 1: Jenkins Script Console (UI)
**Simplest for testing, no command line needed:**

1. Go to `http://<jenkins-url>/script`
2. Copy and paste the content of `jenkins_retention_executor.groovy`
3. Set `dryRun = true` to preview
4. Click "Run"
5. Review the output
6. If satisfied, change `dryRun = false` and run again

---

#### Method 2: Jenkins CLI (Recommended)
**Simple command-line execution without UI:**

```bash
# Download Jenkins CLI (one-time)
wget http://<jenkins-url>/jnlpJars/jenkins-cli.jar

# Execute the script via CLI
java -jar jenkins-cli.jar \
  -s http://<jenkins-url> \
  groovy = < jenkins_retention_executor.groovy
```

**Why this is better:**
- No need to navigate the Jenkins UI
- Easy to schedule with cron
- Output can be captured to a log file
- More scriptable and automation-friendly
- Less prone to UI timeouts on long-running operations

**With authentication (if Jenkins requires it):**
```bash
java -jar jenkins-cli.jar \
  -s http://<jenkins-url> \
  -auth username:apitoken \
  groovy = < jenkins_retention_executor.groovy
```

---

#### Method 3: Pipeline Job
**Integrate into your CI/CD pipeline:**

Create a freestyle or pipeline job with this build step:

```groovy
stage('Maintenance: Cleanup') {
    steps {
        script {
            // Load and execute the retention script
            def script = readFile('jenkins_retention_executor.groovy')
            evaluate(script)
        }
    }
}
```

---

#### Method 4: Scheduled Execution (Cron)
**Automate periodic cleanup:**

Create a shell script `jenkins-cleanup.sh`:

```bash
#!/bin/bash

JENKINS_URL="http://localhost:8080"
SCRIPT_PATH="$(pwd)/jenkins_retention_executor.groovy"
LOG_FILE="/var/log/jenkins-cleanup.log"

echo "$(date): Starting Jenkins retention policy cleanup" >> "$LOG_FILE"

java -jar jenkins-cli.jar \
  -s "$JENKINS_URL" \
  groovy = < "$SCRIPT_PATH" >> "$LOG_FILE" 2>&1

echo "$(date): Cleanup complete" >> "$LOG_FILE"
```

Add to crontab:
```bash
# Run cleanup every Sunday at 2:00 AM
0 2 * * 0 /path/to/jenkins-cleanup.sh
```

---

## Configuration

Edit the top of `jenkins_retention_executor.groovy` to adjust:

```groovy
def config = [
    buildsToKeep: 4,                    // Builds to keep per job
    artifactsToKeep: 2,                 // Builds with artifacts to keep
    dryRun: true,                       // true = preview, false = execute
    deleteOrphanedWorkspaces: true,     // Enable workspace cleanup
    workspaceRoot: "/path/to/workspace" // Workspace directory (adjust if needed)
]
```

---

## Suggested next steps
- Install and test Workspace Cleanup Plugin and/or Artifact Cleanup Plugin if more cleanup is required.
- Try the Jenkins CLI method (Method 2) for easy scheduled execution
- Periodically review disk usage and adjust policies as needed.
- Document any further changes in this sub-task.

---

## Note on Jenkins Agents (Nodes/Slaves)

### Do agents require special treatment for cleanup?

- **No special action is needed**: Jenkins' standard build retention and workspace cleanup mechanisms (including plugins and `cleanWs()`) work the same way on agents as on the master.
- **Builds, workspaces, and artifacts are stored on the agent** where the job runs. When a build is deleted or a workspace is cleaned, the files are removed from the agent.
- **If you use ephemeral agents** (e.g., Docker, cloud VMs), their files are deleted when the agent is destroyed.
- **If you use persistent agents**, monitor disk usage and ensure cleanup policies are in place. You can also manually wipe out a workspace from the Jenkins UI (Node > Workspace > Wipe Out Workspace).
- **Best practice:** Always configure automatic cleanup (build retention, workspace cleanup) in your pipelines to avoid disk space issues on agents.

No special configuration is required for agents beyond what is already described in this document.
