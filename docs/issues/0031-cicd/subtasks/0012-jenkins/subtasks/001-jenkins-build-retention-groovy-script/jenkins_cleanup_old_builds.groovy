// Jenkins Groovy Script: Cleanup Old Builds and Orphaned Workspaces in Multibranch Jobs
// Section 1: Delete old builds, keep only the N most recent per job
// Section 2: Delete orphaned workspaces (folders in workspace root not used by any active job)
// Set dryRun = true to preview what would be deleted without actually deleting anything.
//
// ╔════════════════════════════════════════════════════════════════════════╗
// ║  🪄 THE MAGIC COMMAND (Jenkins CLI - Simplest & Recommended):         ║
// ║                                                                        ║
// ║  java -jar jenkins-cli.jar -s http://<jenkins-url> \                 ║
// ║    groovy = < jenkins_cleanup_old_builds.groovy                      ║
// ║                                                                        ║
// ║  First time: wget http://<jenkins-url>/jnlpJars/jenkins-cli.jar       ║
// ║                                                                        ║
// ║  Why? One command, no UI, easy to automate, no timeouts!              ║
// ╚════════════════════════════════════════════════════════════════════════╝

import jenkins.model.*
import hudson.model.*

def dryRun = true // Set to false to actually delete, true for preview only

def buildsToKeep = 4 // Number of builds to keep per job

println "[INFO] DRY RUN MODE: ${dryRun ? 'ENABLED (no deletions will occur)' : 'DISABLED (deletions will be performed)'}"

// ---
// Section 1: Delete old builds, keep only the N most recent per job
Jenkins.instance.getAllItems(Job.class).each { job ->
    def builds = job.getBuilds().toList() // Make a mutable list
    if (builds.size() > buildsToKeep) {
        builds.sort { it.number } // Sort by build number (ascending)
        def toDelete = builds.take(builds.size() - buildsToKeep)
        toDelete.each { build ->
            if (dryRun) {
                println "[DRY RUN] Would delete build #${build.number} of job ${job.fullName}"
            } else {
                println "Deleting build #${build.number} of job ${job.fullName}"
                build.delete()
            }
        }
    }
}

// ---
// Section 2: Delete orphaned workspaces (folders in workspace root not used by any active job)
// This helps reclaim disk space from jobs/branches that no longer exist in Jenkins.

def workspaceRoot = "${System.getenv('JENKINS_HOME') ?: '/var/jenkins'}/workspace" // Auto-detect Jenkins home

def activeWorkspaces = []
Jenkins.instance.getAllItems(Job.class).each { job ->
    // Only AbstractProject (FreeStyle, Maven, etc.) and similar types have getWorkspace()
    // Pipeline jobs (WorkflowJob) don't support this method directly
    if (job.metaClass.respondsTo(job, 'getWorkspace')) {
        def ws = job.getWorkspace()
        if (ws != null) {
            activeWorkspaces << ws.getRemote()
        }
    }
}

def dir = new File(workspaceRoot)
if (dir.exists()) {
    def allDirs = dir.listFiles().findAll { it.isDirectory() }
    allDirs.each { d ->
        if (!activeWorkspaces.contains(d.absolutePath)) {
            if (dryRun) {
                println "[DRY RUN] Would delete orphan workspace: ${d.absolutePath}"
            } else {
                println "Deleting orphan workspace: ${d.absolutePath}"
                d.deleteDir()
            }
        }
    }
    println dryRun ? "[DRY RUN] Orphan workspace cleanup preview complete." : "Orphan workspace cleanup complete."
} else {
    println "Workspace root not found: ${workspaceRoot}"
}
