# Jenkins Build Retention Utility Script

## Context

In Jenkins multibranch setups, the build retention policy does not always apply correctly to child jobs, which can lead to accumulation of old builds and excessive disk usage. To solve this, you can use a Groovy script in the Jenkins Script Console to delete all old builds, keeping only the N most recent ones per job.

---

## Scriptler Script Metadata (Copy & Paste)

```text
Id: cleanup-old-builds-multibranch
Name: Cleanup Old Builds in Multibranch Jobs
Comment: Deletes all but the N most recent builds in every Jenkins job. Use to enforce build retention in multibranch setups where default policies may fail. Change N as needed.
```

---

## Groovy Script for Cleaning Old Builds

> **Usage:** Copy and paste this script into the Jenkins Script Console (`http://<jenkins>/script`) or save it as a Scriptler script.
> 
> **Caution:** Review the number of builds to keep before running!

```groovy
Jenkins.instance.getAllItems(Job.class).each { job ->
  def builds = job.getBuilds().toList() // Make a mutable list
  if (builds.size() > 4) {
    builds.sort { it.number } // Sort by build number (ascending)
    builds.take(builds.size() - 4).each { it.delete() } // Delete all but the 4 most recent
  }
}
```

- Change the number `4` to the number of builds you want to keep.
- The script iterates over all jobs and deletes old builds.
- It does not delete entire jobs or builds marked as "Keep forever" (lock icon).

---

## How to Schedule Automatic Execution (Scriptler)

You can automate the periodic execution of this Groovy script in Jenkins to ensure old builds are regularly cleaned up, even if the built-in retention policy fails. Here is a recommended approach using Scriptler:

### 1. Create a Freestyle Job
- Go to **"New Item"** in Jenkins.
- Name it, e.g., `auto-cleanup-old-builds`.
- Select **"Freestyle project"** and click OK.

### 2. Configure the Build Trigger
- In the job configuration, find the **"Build Triggers"** section.
- Check **"Build periodically"**.
- Enter the desired cron schedule, e.g.:
  - `@weekly` (once a week)
  - `H 3 * * 1` (every Monday at 3:00)
  - `@daily` (every day)

### 3. Add the Scriptler Build Step
- In the **"Build"** section, click **"Add build step"**.
- Select **"Scriptler script"**.
- Choose your saved script (`cleanup-old-builds-multibranch`).
- Save the job.

### 4. Done!
- Jenkins will now run the script automatically according to your schedule.
- You can view logs for each run in the job's "Builds" tab.

---

## Other Automation Options

- **Groovy Postbuild Plugin:** Run the script as a post-build action in a dedicated maintenance job.
- **Admin Pipeline Job:** Create a dedicated Pipeline job for Jenkins administration and use a `groovy` step to run the script. Schedule the pipeline with a cron trigger.
- **Manual Reminder:** Add a calendar reminder for sysadmins to run the script manually from the Script Console every X weeks/months.

---

## Related
- [Issue 0012: Cleanup and Redeployment](../../plan.md)
- [Manual Cleanup Links](../../manual_cleanup_links.md)
- [Issue 0014: Jenkins Pipeline Containerization](../../../0014-jenkins-pipeline-containerization/index.md)
